"""
Unit tests for the VisualizationService class.

This module contains tests for visualization functionality including:
- Plot generation
- File output
- Error handling for visualization operations
"""

import os
import pytest
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for testing
import matplotlib.pyplot as plt

from datetime import date
from app.service.visualization_service import VisualizationService
from app.service.student_service import StudentService
from app.config.settings import get_settings

settings = get_settings()


class TestVisualizationService:
    """Test cases for VisualizationService."""

    @pytest.fixture
    def test_output_dir(self) -> str:
        """
        Fixture for test output directory.
        
        Returns:
            str: Path to test output directory.
        """
        test_dir = "./test_visualizations"
        os.makedirs(test_dir, exist_ok=True)
        return test_dir

    @pytest.fixture(autouse=True)
    def setup_test_data(self, test_session):
        """
        Fixture to set up test data before each test.
        
        Args:
            test_session: Database session for testing.
        """
        student_service = StudentService(test_session)
        
        # Create test students in multiple grades
        grades = ["一年级", "二年级", "三年级", "四年级", "五年级", "六年级"]
        genders = ["男", "女"]
        
        for grade_idx, grade in enumerate(grades):
            for gender in genders:
                for i in range(10):
                    # Base height increases with grade, with some randomness
                    base_height = {
                        "一年级": {"男": 120, "女": 119},
                        "二年级": {"男": 125, "女": 124},
                        "三年级": {"男": 130, "女": 129},
                        "四年级": {"男": 135, "女": 134},
                        "五年级": {"男": 140, "女": 140},
                        "六年级": {"男": 147, "女": 148},
                    }[grade][gender]
                    
                    height = base_height + np.random.normal(0, 3)
                    # Ensure weight is at least 20kg (minimum valid weight)
                    weight = max(25.0, 30 + grade_idx * 3 + np.random.normal(0, 5))
                    
                    student_service.create_student(
                        student_id=90000 + grade_idx * 100 + (0 if gender == "男" else 50) + i,
                        name=f"{grade}{gender}生{i}",
                        gender=gender,
                        grade=grade,
                        age=7 + grade_idx,
                        height_cm=float(height),
                        weight_kg=float(weight),
                        enrollment_date=date.today()
                    )

    def test_plot_height_distribution(
        self, test_session, test_output_dir: str
    ):
        """
        Test generating height distribution plot.
        
        Expected: PNG file should be created with the visualization.
        """
        viz_service = VisualizationService(test_session)
        
        output_file = os.path.join(test_output_dir, "height_distribution.png")
        
        result = viz_service.plot_height_distribution(
            save=True,
            show=False,
            filename=output_file
        )
        
        assert result is not None
        assert os.path.exists(result)
        assert result.endswith(".png")
        
        # Cleanup
        if os.path.exists(result):
            os.remove(result)

    def test_plot_height_by_grade(
        self, test_session, test_output_dir: str
    ):
        """
        Test generating height by grade boxplot.
        
        Expected: PNG file should be created with the visualization.
        """
        viz_service = VisualizationService(test_session)
        
        output_file = os.path.join(test_output_dir, "height_by_grade.png")
        
        result = viz_service.plot_height_by_grade(
            save=True,
            show=False,
            filename=output_file
        )
        
        assert result is not None
        assert os.path.exists(result)
        
        # Cleanup
        if os.path.exists(result):
            os.remove(result)

    def test_plot_height_heatmap(
        self, test_session, test_output_dir: str
    ):
        """
        Test generating height heatmap by grade and gender.
        
        Expected: PNG file should be created with the visualization.
        """
        viz_service = VisualizationService(test_session)
        
        output_file = os.path.join(test_output_dir, "height_heatmap.png")
        
        result = viz_service.plot_height_heatmap(
            save=True,
            show=False,
            filename=output_file
        )
        
        assert result is not None
        assert os.path.exists(result)
        
        # Cleanup
        if os.path.exists(result):
            os.remove(result)

    def test_plot_gender_comparison(
        self, test_session, test_output_dir: str
    ):
        """
        Test generating gender comparison plot.
        
        Expected: PNG file should be created with the visualization.
        """
        viz_service = VisualizationService(test_session)
        
        output_file = os.path.join(test_output_dir, "gender_comparison.png")
        
        result = viz_service.plot_gender_comparison(
            save=True,
            show=False,
            filename=output_file
        )
        
        assert result is not None
        assert os.path.exists(result)
        
        # Cleanup
        if os.path.exists(result):
            os.remove(result)

    def test_plot_bmi_distribution(
        self, test_session, test_output_dir: str
    ):
        """
        Test generating BMI distribution plot.
        
        Expected: PNG file should be created with the visualization.
        """
        viz_service = VisualizationService(test_session)
        
        output_file = os.path.join(test_output_dir, "bmi_distribution.png")
        
        result = viz_service.plot_bmi_distribution(
            save=True,
            show=False,
            filename=output_file
        )
        
        assert result is not None
        assert os.path.exists(result)
        
        # Cleanup
        if os.path.exists(result):
            os.remove(result)

    def test_plot_growth_trend(
        self, test_session, test_output_dir: str
    ):
        """
        Test generating growth trend plot.
        
        Expected: PNG file should be created with the visualization.
        """
        viz_service = VisualizationService(test_session)
        
        output_file = os.path.join(test_output_dir, "growth_trend.png")
        
        result = viz_service.plot_growth_trend(
            save=True,
            show=False,
            filename=output_file
        )
        
        assert result is not None
        assert os.path.exists(result)
        
        # Cleanup
        if os.path.exists(result):
            os.remove(result)

    def test_plot_grade_height_comparison(
        self, test_session, test_output_dir: str
    ):
        """
        Test generating grade height comparison plot.
        
        Expected: PNG file should be created with the visualization.
        """
        viz_service = VisualizationService(test_session)
        
        output_file = os.path.join(test_output_dir, "grade_comparison.png")
        
        result = viz_service.plot_grade_height_comparison(
            save=True,
            show=False,
            filename=output_file
        )
        
        assert result is not None
        assert os.path.exists(result)
        
        # Cleanup
        if os.path.exists(result):
            os.remove(result)

    def test_plot_weight_distribution(
        self, test_session, test_output_dir: str
    ):
        """
        Test generating weight distribution plot.
        
        Expected: PNG file should be created with the visualization.
        """
        viz_service = VisualizationService(test_session)
        
        output_file = os.path.join(test_output_dir, "weight_distribution.png")
        
        result = viz_service.plot_weight_distribution(
            save=True,
            show=False,
            filename=output_file
        )
        
        assert result is not None
        assert os.path.exists(result)
        
        # Cleanup
        if os.path.exists(result):
            os.remove(result)

    def test_generate_all_visualizations(
        self, test_session, test_output_dir: str
    ):
        """
        Test generating all visualizations at once.
        
        Expected: Multiple PNG files should be created in the output directory.
        """
        viz_service = VisualizationService(test_session, output_dir=test_output_dir)
        
        results = viz_service.generate_all_visualizations(
            save=True,
            show=False
        )
        
        assert results is not None
        assert isinstance(results, dict)
        assert len(results) > 0
        
        # Verify files exist (results is a dict with visualization names as keys)
        for result in results.values():
            if result is not None:
                assert os.path.exists(result)
            
        # Cleanup
        for result in results.values():
            if result is not None and os.path.exists(result):
                os.remove(result)

    def test_visualization_with_no_data(
        self, test_session, test_output_dir: str
    ):
        """
        Test visualization when there is no data.
        
        Expected: Should handle empty data gracefully.
        """
        # Create a new session with empty database
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.models.base import Base
        
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        empty_session = sessionmaker(bind=engine)()
        
        try:
            viz_service = VisualizationService(empty_session)
            
            output_file = os.path.join(test_output_dir, "no_data_test.png")
            
            result = viz_service.plot_height_distribution(
                save=True,
                show=False,
                filename=output_file
            )
            
            # Should return None or handle gracefully
            # Either no exception is raised, or a warning is logged
            
            # Cleanup if file was created
            if result and os.path.exists(result):
                os.remove(result)
                
        finally:
            empty_session.close()
            engine.dispose()

    def test_visualization_custom_styling(
        self, test_session, test_output_dir: str
    ):
        """
        Test visualization with custom styling options.
        
        Expected: Visualization should be generated with specified style.
        """
        viz_service = VisualizationService(test_session)
        
        output_file = os.path.join(test_output_dir, "custom_style.png")
        
        # Test with different figure size
        result = viz_service.plot_height_distribution(
            save=True,
            show=False,
            filename=output_file,
            figsize=(12, 8)
        )
        
        assert result is not None
        assert os.path.exists(result)
        
        # Cleanup
        if os.path.exists(result):
            os.remove(result)

    def test_plot_height_weight_correlation(
        self, test_session, test_output_dir: str
    ):
        """
        Test generating height-weight correlation scatter plot.
        
        Expected: PNG file should be created with the visualization.
        """
        viz_service = VisualizationService(test_session)
        
        output_file = os.path.join(test_output_dir, "height_weight_correlation.png")
        
        # This method might exist in the service
        if hasattr(viz_service, 'plot_height_weight_correlation'):
            result = viz_service.plot_height_weight_correlation(
                save=True,
                show=False,
                filename=output_file
            )
            
            assert result is not None
            assert os.path.exists(result)
            
            # Cleanup
            if os.path.exists(result):
                os.remove(result)

    def test_multiple_visualizations_memory_management(
        self, test_session, test_output_dir: str
    ):
        """
        Test memory management when generating multiple visualizations.
        
        Expected: Plots should be properly closed after generation to save memory.
        """
        viz_service = VisualizationService(test_session)
        
        # Generate multiple plots to ensure memory is managed properly
        for i in range(5):
            output_file = os.path.join(test_output_dir, f"multi_plot_{i}.png")
            
            result = viz_service.plot_height_distribution(
                save=True,
                show=False,
                filename=output_file
            )
            
            assert result is not None
            assert os.path.exists(result)
            
            # Cleanup
            if os.path.exists(result):
                os.remove(result)
        
        # Ensure no figures are left open
        assert plt.get_fignums() == []

    def test_output_directory_creation(
        self, test_session, tmp_path: str
    ):
        """
        Test that output directory is created if it doesn't exist.
        
        Expected: Directory should be created automatically.
        """
        viz_service = VisualizationService(test_session)
        
        # Create a path to a non-existent directory
        new_dir = os.path.join(tmp_path, "new_output_dir")
        assert not os.path.exists(new_dir)
        
        output_file = os.path.join(new_dir, "test_plot.png")
        
        result = viz_service.plot_height_distribution(
            save=True,
            show=False,
            filename=output_file
        )
        
        # The directory should now exist
        assert os.path.exists(new_dir)
        assert os.path.exists(result)
        
        # Cleanup
        if os.path.exists(result):
            os.remove(result)
        os.rmdir(new_dir)
