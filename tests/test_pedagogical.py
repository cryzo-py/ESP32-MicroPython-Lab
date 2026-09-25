"""
Tests unitaires pour le cursus pédagogique et le moteur d'évaluation automatique
"""

import pytest
from esp32_lab.core.courses import Lesson, get_course_curriculum
from esp32_lab.core.evaluator import ExerciseEvaluator
from esp32_lab.core.examples import create_blink_example
from esp32_lab.core.models.project import ProjectModel
from esp32_lab.ui.dialogs.courses_dialog import CoursesDialog


def test_course_curriculum():
    lessons = get_course_curriculum()
    assert len(lessons) >= 8
    
    lesson_ids = [l.id for l in lessons]
    assert "lesson_1_gpio_led" in lesson_ids
    assert "lesson_2_button" in lesson_ids
    assert "lesson_3_pot_adc" in lesson_ids
    assert "lesson_4_servo_pwm" in lesson_ids
    assert "lesson_5_dht22" in lesson_ids
    assert "lesson_6_oled" in lesson_ids
    assert "lesson_7_hcsr04" in lesson_ids
    assert "lesson_8_lcd" in lesson_ids

    for lesson in lessons:
        assert lesson.title
        assert lesson.theory
        assert lesson.challenge
        assert lesson.starter_project is not None
        assert len(lesson.starter_project.get_main_code()) > 0


def test_evaluator_perfect_project():
    lessons = get_course_curriculum()
    lesson_1 = next(l for l in lessons if l.id == "lesson_1_gpio_led")
    evaluator = ExerciseEvaluator()

    # The starter project is pre-wired and coded correctly
    result = evaluator.evaluate(lesson_1, lesson_1.starter_project)
    assert result.passed is True
    assert result.score == 100
    assert result.percentage == 100
    for crit in result.criteria:
        assert crit.passed is True


def test_evaluator_syntax_error():
    lessons = get_course_curriculum()
    lesson_1 = next(l for l in lessons if l.id == "lesson_1_gpio_led")
    evaluator = ExerciseEvaluator()

    bad_proj = create_blink_example()
    bad_proj.set_main_code("while True def invalid syntax error !!!")

    result = evaluator.evaluate(lesson_1, bad_proj)
    assert result.passed is False
    assert result.score < 70
    syntax_crit = next(c for c in result.criteria if c.id == "syntax")
    assert syntax_crit.passed is False


def test_evaluator_missing_components():
    lessons = get_course_curriculum()
    lesson_1 = next(l for l in lessons if l.id == "lesson_1_gpio_led")
    evaluator = ExerciseEvaluator()

    empty_proj = ProjectModel(name="Vide", files={"main.py": lesson_1.starter_project.get_main_code()})
    result = evaluator.evaluate(lesson_1, empty_proj)
    assert result.passed is False
    comp_crit = next(c for c in result.criteria if c.id == "components")
    assert comp_crit.passed is False
    wiring_crit = next(c for c in result.criteria if c.id == "wiring")
    assert wiring_crit.passed is False




def test_courses_dialog(app):
    lessons = get_course_curriculum()
    proj = create_blink_example()
    dlg = CoursesDialog(proj)

    assert dlg.list_widget.count() == len(lessons)
    dlg.list_widget.setCurrentRow(1)
    assert "TP 2" in dlg.lbl_title.text()

    # Test evaluation inside dialog
    dlg._run_evaluation()
    assert not dlg.eval_details_browser.isHidden()
    assert len(dlg.eval_details_browser.toHtml()) > 0
    dlg.close()
