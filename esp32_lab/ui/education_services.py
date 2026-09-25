# -*- coding: utf-8 -*-
from esp32_lab.core.session_repository import SQLiteSessionRepository
from esp32_lab.core.submission_repository import SQLiteSubmissionRepository
from esp32_lab.core.activity_session_service import ActivitySessionService
from esp32_lab.core.teacher_review_service import TeacherReviewService
from esp32_lab.core.app_state import AppState

def inject_services(main_window):
    # Setup AppState if not exists
    if not hasattr(main_window, 'app_state'):
        main_window.app_state = AppState()
        
    if getattr(main_window, "app_profile", "student") == "teacher":
        main_window.app_state.activate_teacher_mode()
        
    # Setup Repos
    sess_repo = SQLiteSessionRepository()
    sub_repo = SQLiteSubmissionRepository()
    
    # Setup Services
    main_window.session_service = ActivitySessionService(sess_repo, submission_repo=sub_repo)
    main_window.teacher_review_service = TeacherReviewService(sub_repo, main_window.app_state)
    

    # Attach to UI
    if hasattr(main_window, 'activity_panel'):
        main_window.activity_panel.attach_service(
            main_window.session_service, 
            is_teacher=main_window.app_state.is_teacher_mode_active()
        )
        
    # We should update activity_panel when teacher mode changes
    def _on_mode_change(mode):
        from esp32_lab.core.app_state import AppMode
        is_teacher = (mode == AppMode.TEACHER)
        if hasattr(main_window, 'activity_panel'):
            main_window.activity_panel.attach_service(
                main_window.session_service, 
                is_teacher=is_teacher
            )
            main_window.activity_panel._update_session_ui()
            
    main_window.app_state.on_mode_changed(_on_mode_change)
    
    # Sync InteractionPolicy AppState
    if hasattr(main_window, 'circuit_scene'):
        main_window.circuit_scene.interaction_policy.set_app_state(main_window.app_state)
