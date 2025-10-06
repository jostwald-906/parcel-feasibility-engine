"""
Tests for RHNA Data Service

These tests verify the RHNA service correctly loads and queries
SB35 affordability determinations from HCD data.
"""

import pytest
from pathlib import Path
from app.services.rhna_service import RHNADataService


class TestRHNADataService:
    """Test suite for RHNA data service."""

    @pytest.fixture
    def service(self):
        """Create service instance with actual data."""
        return RHNADataService()

    def test_service_initialization(self, service):
        """Test that service initializes correctly."""
        assert service is not None
        assert service.data_file is not None
        assert isinstance(service.cache, dict)

    def test_data_file_exists(self, service):
        """Test that data file exists and is loaded."""
        # If data file doesn't exist, cache should be empty
        if not service.data_file.exists():
            assert len(service.cache) == 0
            pytest.skip("Data file not found - skipping data-dependent tests")
        else:
            assert len(service.cache) > 0

    def test_get_summary_stats(self, service):
        """Test summary statistics."""
        stats = service.get_summary_stats()

        assert 'total_jurisdictions' in stats
        assert 'exempt_count' in stats
        assert 'requires_10_pct_count' in stats
        assert 'requires_50_pct_count' in stats

        if service.data_file.exists():
            # Should have data for California jurisdictions
            assert stats['total_jurisdictions'] > 0
            # Sum of categories should equal total (roughly)
            total_categorized = (
                stats['exempt_count'] +
                stats['requires_10_pct_count'] +
                stats['requires_50_pct_count']
            )
            assert total_categorized == stats['total_jurisdictions']

    def test_known_high_performing_jurisdiction(self, service):
        """Test known high-performing jurisdiction (San Francisco)."""
        result = service.get_sb35_affordability("San Francisco")

        assert result is not None
        assert 'percentage' in result
        assert 'income_levels' in result
        assert 'source' in result
        assert 'notes' in result

        # Check that result is valid (could be 0%, 10%, or 50% based on actual HCD data)
        assert result['percentage'] in [0.0, 10.0, 50.0]

    def test_known_low_performing_jurisdiction(self, service):
        """Test jurisdiction with HCD data."""
        # Test with Adelanto (any jurisdiction in the dataset)
        result = service.get_sb35_affordability("Adelanto")

        assert result is not None
        assert 'percentage' in result

        # Should return one of the valid percentages based on actual HCD data
        assert result['percentage'] in [0.0, 10.0, 50.0]

    def test_case_insensitive_lookup(self, service):
        """Test that jurisdiction lookup is case-insensitive."""
        # Try different case variations
        result1 = service.get_sb35_affordability("LOS ANGELES")
        result2 = service.get_sb35_affordability("Los Angeles")
        result3 = service.get_sb35_affordability("los angeles")

        # Should all return same result
        assert result1['percentage'] == result2['percentage']
        assert result2['percentage'] == result3['percentage']

    def test_unknown_jurisdiction_fallback(self, service):
        """Test fallback behavior for unknown jurisdiction."""
        result = service.get_sb35_affordability("Totally Fake City")

        assert result is not None
        assert 'percentage' in result
        # Should use fallback logic (conservative 50% or 10% for known high performers)
        assert result['percentage'] in [10.0, 50.0]
        # Should indicate it's estimated
        assert 'Estimated' in result['source'] or 'estimated' in result['source'].lower()

    def test_exempt_jurisdiction(self, service):
        """Test jurisdiction that is exempt from SB35."""
        if not service.data_file.exists():
            pytest.skip("Data file not found")

        # Find an exempt jurisdiction in the data
        exempt_jurisdictions = [
            data['jurisdiction']
            for data in service.cache.values()
            if data.get('is_exempt') and ' - ' not in data.get('jurisdiction', '')
        ]

        if exempt_jurisdictions:
            result = service.get_sb35_affordability(exempt_jurisdictions[0])
            assert result['percentage'] == 0.0
            assert result['is_exempt'] is True
            assert 'EXEMPT' in ' '.join(result['notes']).upper()

    def test_10_percent_requirement(self, service):
        """Test jurisdiction with 10% affordability requirement."""
        if not service.data_file.exists():
            pytest.skip("Data file not found")

        # Find a jurisdiction with 10% requirement
        ten_pct_jurisdictions = [
            data['jurisdiction']
            for data in service.cache.values()
            if data.get('requires_10_pct') and ' - ' not in data.get('jurisdiction', '')
        ]

        if ten_pct_jurisdictions:
            result = service.get_sb35_affordability(ten_pct_jurisdictions[0])
            assert result['percentage'] == 10.0
            assert 'Lower Income' in result['income_levels']
            assert result['is_exempt'] is False

    def test_50_percent_requirement(self, service):
        """Test jurisdiction with 50% affordability requirement."""
        if not service.data_file.exists():
            pytest.skip("Data file not found")

        # Find a jurisdiction with 50% requirement
        fifty_pct_jurisdictions = [
            data['jurisdiction']
            for data in service.cache.values()
            if data.get('requires_50_pct') and ' - ' not in data.get('jurisdiction', '')
        ]

        if fifty_pct_jurisdictions:
            result = service.get_sb35_affordability(fifty_pct_jurisdictions[0])
            assert result['percentage'] == 50.0
            assert len(result['income_levels']) > 0
            # Should include Very Low Income and Lower Income
            assert any('Very Low' in level for level in result['income_levels'])
            assert result['is_exempt'] is False

    def test_list_jurisdictions(self, service):
        """Test listing all jurisdictions."""
        if not service.data_file.exists():
            pytest.skip("Data file not found")

        jurisdictions = service.list_jurisdictions()

        assert isinstance(jurisdictions, list)
        assert len(jurisdictions) > 0

        # Check structure
        if jurisdictions:
            first = jurisdictions[0]
            assert 'jurisdiction' in first
            assert 'county' in first
            assert 'affordability_pct' in first
            assert 'is_exempt' in first

    def test_list_jurisdictions_with_county_filter(self, service):
        """Test listing jurisdictions filtered by county."""
        if not service.data_file.exists():
            pytest.skip("Data file not found")

        # List all Los Angeles County jurisdictions
        la_jurisdictions = service.list_jurisdictions(county="Los Angeles")

        assert isinstance(la_jurisdictions, list)

        # All should be in Los Angeles County
        for juris in la_jurisdictions:
            assert juris['county'].upper() == "LOS ANGELES"

    def test_above_moderate_progress_data(self, service):
        """Test that above-moderate progress data is included."""
        if not service.data_file.exists():
            pytest.skip("Data file not found")

        result = service.get_sb35_affordability("Los Angeles")

        assert 'above_moderate_progress' in result
        # May be None if data not available, or a number
        if result['above_moderate_progress'] is not None:
            assert isinstance(result['above_moderate_progress'], (int, float))
            assert result['above_moderate_progress'] >= 0

    def test_notes_include_verification_warning(self, service):
        """Test that all results include verification warnings."""
        result = service.get_sb35_affordability("San Francisco")

        # Notes should include disclaimer to verify with planning department
        notes_text = ' '.join(result['notes']).upper()
        assert 'VERIFY' in notes_text or 'VERIFICATION' in notes_text

    def test_notes_include_data_source(self, service):
        """Test that results include data source information."""
        result = service.get_sb35_affordability("Los Angeles")

        # Should include data source in notes
        notes_text = ' '.join(result['notes'])
        assert 'HCD' in notes_text or 'data.ca.gov' in notes_text or result['source']

    def test_county_disambiguation(self, service):
        """Test that county parameter helps with disambiguation."""
        if not service.data_file.exists():
            pytest.skip("Data file not found")

        # Some jurisdiction names may exist in multiple counties
        # Providing county should help disambiguate
        result = service.get_sb35_affordability(
            jurisdiction="Alameda",
            county="Alameda"
        )

        assert result is not None
        assert 'county' in result
        # Should match the requested county (case-insensitive)
        if result['county'].upper() != "UNKNOWN":
            assert result['county'].upper() == "ALAMEDA"


class TestRHNAServiceIntegrationWithSB35:
    """Integration tests with SB35 code."""

    def test_sb35_uses_rhna_service(self):
        """Test that SB35 code integrates with RHNA service."""
        from app.rules.state_law.sb35 import get_affordability_requirement
        from app.models.parcel import ParcelBase

        # Create test parcel
        parcel = ParcelBase(
            apn="123-456-789",
            address="123 Test St",
            city="Los Angeles",
            county="Los Angeles",
            state="CA",
            zip_code="90001",
            lot_size_sqft=10000,
            zoning_code="R3",
            existing_units=0,
            existing_building_sqft=0
        )

        result = get_affordability_requirement(parcel)

        # Should return valid result
        assert result is not None
        assert 'percentage' in result
        assert 'income_levels' in result
        assert 'notes' in result

        # Percentage should be valid
        assert result['percentage'] in [0.0, 10.0, 50.0]

    def test_rhna_status_check(self):
        """Test RHNA status check function."""
        from app.rules.state_law.sb35 import _check_rhna_status
        from app.models.parcel import ParcelBase

        parcel = ParcelBase(
            apn="123-456-789",
            address="123 Test St",
            city="San Francisco",
            county="San Francisco",
            state="CA",
            zip_code="94102",
            lot_size_sqft=10000,
            zoning_code="R3",
            existing_units=0,
            existing_building_sqft=0
        )

        result = _check_rhna_status(parcel)

        assert 'on_track' in result
        assert 'performance_level' in result
        assert isinstance(result['on_track'], bool)
        assert result['performance_level'] in ['high', 'low']


class TestRHNAServiceEdgeCases:
    """Test edge cases and error handling."""

    def test_service_with_missing_data_file(self):
        """Test service behavior when data file is missing."""
        service = RHNADataService(data_file="nonexistent/path/file.csv")

        # Should initialize without crashing
        assert service is not None

        # Cache should be empty
        assert len(service.cache) == 0

        # Should fall back gracefully
        result = service.get_sb35_affordability("Any City")
        assert result is not None
        assert result['percentage'] in [10.0, 50.0]

    def test_empty_jurisdiction_name(self):
        """Test with empty jurisdiction name."""
        service = RHNADataService()
        result = service.get_sb35_affordability("")

        # Should fall back gracefully
        assert result is not None
        assert 'percentage' in result

    def test_whitespace_in_jurisdiction_name(self):
        """Test jurisdiction name with extra whitespace."""
        service = RHNADataService()
        result = service.get_sb35_affordability("  Los Angeles  ")

        # Should handle whitespace correctly
        assert result is not None
        assert 'percentage' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
