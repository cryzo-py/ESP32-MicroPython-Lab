# -*- coding: utf-8 -*-
import json
import copy
from typing import Optional, Tuple
from .clock import Clock, SystemClock
from .models.activity_session import ActivitySession, SessionState, StudentIdentity
from .session_repository import SessionRepository
from .models.project import ProjectModel
from .models.pedagogical_activity import ActivityContext, ActivityType
from .models.submission import Submission, SubmissionReason, SubmissionStatus
from .submission_repository import SubmissionRepository
from .submission_evaluation_service import SubmissionEvaluationService

class ActivitySessionService:
    def __init__(self, 
                 repository: SessionRepository, 
                 clock: Clock = None, 
                 submission_repo: SubmissionRepository = None):
        self.repository = repository
        self.clock = clock or SystemClock()
        self.submission_repo = submission_repo
        self.eval_service = SubmissionEvaluationService() if submission_repo else None
        
        self.current_session: Optional[ActivitySession] = None
        self.session_project: Optional[ProjectModel] = None
        self.subject_pedagogy_profile: dict = {}

    def load_or_create_session(self, 
                               subject_project: ProjectModel, 
                               student: Optional[StudentIdentity] = None) -> Tuple[ActivitySession, ProjectModel]:
        ctx = ActivityContext(subject_project.pedagogy_profile)
        if not ctx.has_activity:
            raise ValueError("Le projet n'est pas une activité pédagogique.")
            
        self.subject_pedagogy_profile = copy.deepcopy(subject_project.pedagogy_profile)
            
        activity_id = ctx.activity.get("id", "")
        student_id = student.student_id if student else ""
        
        act_type = ctx.activity_type
        strict_mode = ctx.activity.get("settings", {}).get("strict_mode", False)
        if act_type == ActivityType.EXAM and strict_mode and not student:
            raise ValueError("Une identité est requise pour cet examen.")

        existing = self.repository.find_active_session(activity_id, student_id)
        
        if existing:
            self.current_session = existing
            working_proj_json = self.repository.get_working_project(existing.session_id)
            if working_proj_json:
                state = json.loads(working_proj_json)
                proj = ProjectModel.from_dict(state)
                if not proj.pedagogy_profile:
                    proj.pedagogy_profile = copy.deepcopy(subject_project.pedagogy_profile)
                self.session_project = proj
            else:
                self._create_working_copy(subject_project)
                
            self._update_session_state()
        else:
            self.current_session = ActivitySession(activity_id=activity_id, student=student)
            self._create_working_copy(subject_project)
            self.repository.save(self.current_session, json.dumps(self.session_project.to_dict()))

        return self.current_session, self.session_project

    def _create_working_copy(self, subject_project: ProjectModel):
        state = copy.deepcopy(subject_project.to_dict())
        self.session_project = ProjectModel.from_dict(state)

    def start_session(self):
        if not self.current_session: return
        if self.current_session.status != SessionState.NOT_STARTED: return 
            
        now = self.clock.now()
        self.current_session.started_at = now
        self.current_session.status = SessionState.IN_PROGRESS
        
        ctx = ActivityContext(self.session_project.pedagogy_profile)
        duration = ctx.activity.get("duration_minutes", 0)
        if duration > 0:
            self.current_session.deadline = now + (duration * 60)
            
        self.autosave()

    def update_and_get_remaining_time(self) -> Optional[int]:
        if not self.current_session or self.current_session.status not in (SessionState.IN_PROGRESS, SessionState.EXPIRED):
            return None
        self._update_session_state()
        if self.current_session.deadline:
            return max(0, int(self.current_session.deadline - self.clock.now()))
        return None

    def _update_session_state(self):
        if self.current_session.status == SessionState.IN_PROGRESS and self.current_session.deadline:
            if self.clock.now() >= self.current_session.deadline:
                self.current_session.status = SessionState.EXPIRED
                self.autosave()
                self.freeze_session() # Ensures freeze even if _create_submission returns early
                self._create_submission(SubmissionReason.TIMEOUT_AUTO_SUBMIT)

    def request_freeze(self):
        if self.current_session and self.current_session.status == SessionState.IN_PROGRESS:
            self.current_session.status = SessionState.FROZEN
            self.autosave()
            self._create_submission(SubmissionReason.STUDENT_SUBMIT)

    def freeze_session(self):
        if self.current_session and self.current_session.status == SessionState.EXPIRED:
            self.current_session.status = SessionState.FROZEN
            self.autosave()

    def autosave(self):
        if self.current_session and self.session_project:
            self.repository.save(self.current_session, json.dumps(self.session_project.to_dict()))
            
    def restart_session(self, subject_project: ProjectModel):
        if not self.current_session:
            return
        
        # Effacer l'ancienne session
        self.repository.delete(self.current_session.session_id)
        if self.submission_repo:
            sub = self.submission_repo.find_by_session(self.current_session.session_id)
            if sub:
                self.submission_repo.delete(sub.submission_id)
                
        # Recréer une nouvelle session
        self.current_session = ActivitySession(
            activity_id=self.current_session.activity_id, 
            student=self.current_session.student
        )
        self._create_working_copy(subject_project)
        self.autosave()
            
    def get_session(self) -> Optional[ActivitySession]:
        return self.current_session

    def _create_submission(self, reason: SubmissionReason):
        if not self.submission_repo or not self.current_session:
            return
            
        existing = self.submission_repo.find_by_session(self.current_session.session_id)
        if existing:
            return
            
        self.freeze_session()
            
        submission = Submission(
            session_id=self.current_session.session_id,
            activity_id=self.current_session.activity_id,
            student_identity=self.current_session.student,
            submitted_at=self.clock.now(),
            submission_reason=reason,
            snapshot=copy.deepcopy(self.session_project.to_dict())
        )
        
        self.submission_repo.save(submission)
        
        submission = self.eval_service.evaluate(submission, self.subject_pedagogy_profile)
        self.submission_repo.save(submission)
