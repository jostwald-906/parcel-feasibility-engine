# React Components - AI Agent Context

## Overview

React components for the Parcel Feasibility Engine frontend. All components use TypeScript, Tailwind CSS v4, and follow Next.js 15 client component patterns.

**Component Philosophy**:
- Single responsibility
- Reusable and composable
- Type-safe with TypeScript
- Accessible (ARIA labels, keyboard navigation)
- Responsive design (mobile-first)

## Component List

```
components/
├── ParcelForm.tsx               # Main analysis form (multi-step)
├── ParcelMap.tsx                # Interactive Leaflet map
├── ParcelMapWrapper.tsx         # Client-side map loader
├── ParcelInfoPanel.tsx          # GIS data display panel
├── ParcelAutocomplete.tsx       # APN search with autocomplete
├── MultiParcelSelector.tsx      # Multiple parcel selection UI
├── ProposedProjectForm.tsx      # Proposed project details form
├── ResultsDashboard.tsx         # Analysis results display
├── ScenarioComparison.tsx       # Development scenario cards
├── CNELDisplayCard.tsx          # Noise analysis visualization
├── CommunityBenefitsCard.tsx    # Community benefits display
└── OverlayDetailCard.tsx        # Overlay zone details
```

## Critical Patterns

### Client Component Directive

All interactive components MUST use `'use client'`:

```typescript
'use client';

import { useState } from 'react';

export default function ParcelForm() {
  // Component logic
}
```

### Text Input Pattern (CRITICAL)

**ALL text inputs MUST include `text-gray-900` className**:

```typescript
<input
  type="text"
  name="apn"
  value={formData.apn}
  onChange={handleInputChange}
  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
  placeholder="4276-019-030"
  required
/>
```

**Why**: Without `text-gray-900`, text appears white on white background (invisible).

### Number Input Pattern

```typescript
<input
  type="number"
  name="lot_size_sqft"
  value={formData.lot_size_sqft || ''}
  onChange={handleInputChange}
  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
  placeholder="5000"
  required
  min="0"
  step="1"
/>
```

### Select Pattern

```typescript
<select
  name="zoning_code"
  value={formData.zoning_code}
  onChange={handleInputChange}
  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
  required
>
  <option value="">Select zoning...</option>
  {ZONING_CODES.map(zone => (
    <option key={zone.code} value={zone.code}>
      {zone.code} - {zone.description}
    </option>
  ))}
</select>
```

## Component Details

### ParcelForm.tsx

**Purpose**: Multi-step form for parcel analysis with validation and auto-population from GIS data.

**Key Features**:
- 5-step organization (Site ID, Characteristics, Existing Conditions, Proposed Project, Analysis Options)
- Auto-population from ParcelAutocomplete or map selection
- Dynamic form validation
- Eligibility checks for SB 9, SB 35, AB 2011
- Contextual help and warnings

**Props**:
```typescript
interface ParcelFormProps {
  onSubmit: (request: AnalysisRequest) => void;
  isLoading?: boolean;
  initialData?: ParcelAnalysis | null;
}
```

**State Management**:
```typescript
const [formData, setFormData] = useState<Partial<Parcel>>({
  apn: '',
  address: '',
  city: 'Santa Monica',
  county: 'Los Angeles',
  zip_code: '',
  lot_size_sqft: undefined,
  zoning_code: 'R1',
  existing_units: 0,
  existing_building_sqft: 0,
  // ...
});

const [options, setOptions] = useState({
  include_sb9: true,
  include_sb35: true,
  include_ab2011: false,
  include_density_bonus: true,
  target_affordability_pct: 15,
});
```

**Auto-population from GIS**:
```typescript
useEffect(() => {
  if (initialData) {
    setFormData({
      apn: initialData.parcel.apn || '',
      address: initialData.parcel.address || '',
      // Map GIS data to form fields
      zoning_code: initialData.zoning.zoneCode || 'R1',
      lot_size_sqft: initialData.parcel.lotSizeSqft || undefined,
      // Environmental flags
      in_coastal_zone: initialData.coastal.inCoastalZone,
      is_historic_property: initialData.historic.isHistoric,
      // ...
    });
  }
}, [initialData]);
```

**Eligibility Checks**:
```typescript
// Helper: Check SB 9 eligibility
const isSB9Eligible = (data?: ParcelAnalysis | null, zoningCode?: string): boolean => {
  const zoning = zoningCode || data?.zoning.zoneCode || formData.zoning_code || '';

  // Must be single-family zoning
  if (!isSingleFamilyZoning(zoning)) {
    return false;
  }

  // Cannot be historic
  if (data?.historic.isHistoric) {
    return false;
  }

  return true;
};

// Helper: Check AB 2011 eligibility
const isAB2011Eligible = (data?: ParcelAnalysis | null, zoningCode?: string): boolean => {
  const zoning = zoningCode || data?.zoning.zoneCode || formData.zoning_code || '';

  // Must be commercial/office/mixed-use
  if (!isCommercialZoning(zoning)) {
    return false;
  }

  // Cannot be historic
  if (data?.historic.isHistoric) {
    return false;
  }

  return true;
};
```

**Conditional Rendering**:
```typescript
<label className={`flex items-start gap-3 p-3 border border-gray-200 rounded-lg transition-colors ${
  isSB9Eligible(initialData, formData.zoning_code)
    ? 'hover:bg-gray-50 cursor-pointer'
    : 'bg-gray-50 cursor-not-allowed'
}`}>
  <input
    type="checkbox"
    name="include_sb9"
    checked={options.include_sb9}
    onChange={handleOptionChange}
    disabled={!isSB9Eligible(initialData, formData.zoning_code)}
    className="w-4 h-4 mt-0.5 text-blue-600 rounded disabled:opacity-50"
  />
  <div className="flex-1">
    <span className={`text-sm font-medium ${
      !isSB9Eligible(initialData, formData.zoning_code) ? 'text-gray-400' : 'text-gray-900'
    }`}>
      SB 9 (2021) - Lot Splits & Duplexes
    </span>
    <p className="text-xs text-gray-600 mt-1">
      Up to 4 units on single-family lots
      {!isSB9Eligible(initialData, formData.zoning_code) &&
        ` (Not eligible - ${getSB9ExclusionReason(initialData, formData.zoning_code)})`
      }
    </p>
  </div>
</label>
```

### ParcelMap.tsx

**Purpose**: Interactive Leaflet map for parcel selection with boundary visualization.

**Key Features**:
- Click to select parcels
- Parcel boundary overlay
- Zoning layer toggle
- Transit stops layer
- Custom tooltips

**Critical**: Map overlays must use `z-[1000]` to appear above tiles:

```typescript
'use client';

import { MapContainer, TileLayer, Polygon, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

export default function ParcelMap({ onParcelSelected, height = "500px" }) {
  const [selectedBoundary, setSelectedBoundary] = useState<L.LatLngExpression[] | null>(null);

  return (
    <div className="relative">
      <MapContainer
        center={[34.0195, -118.4912]}  // Santa Monica
        zoom={13}
        style={{ height, width: '100%' }}
        className="rounded-lg z-0"
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap contributors'
        />

        {/* Parcel boundary overlay - MUST use z-[1000] */}
        {selectedBoundary && (
          <Polygon
            positions={selectedBoundary}
            pathOptions={{
              color: '#3b82f6',
              fillColor: '#3b82f6',
              fillOpacity: 0.2,
              weight: 3
            }}
            // Pane with high z-index
            pane="overlayPane"
          />
        )}
      </MapContainer>

      {/* Loading overlay - z-[1000] to appear above map */}
      {isLoading && (
        <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-[1000]">
          <div className="text-gray-600">Loading parcel data...</div>
        </div>
      )}
    </div>
  );
}
```

**Custom Pane Creation**:
```typescript
function MapPaneSetup() {
  const map = useMap();

  useEffect(() => {
    // Create custom pane with high z-index
    const pane = map.createPane('parcels');
    pane.style.zIndex = '1000';
  }, [map]);

  return null;
}
```

### ParcelAutocomplete.tsx

**Purpose**: APN search with debounced autocomplete and GIS data preview.

**Key Features**:
- Debounced search (300ms)
- Real-time suggestions
- GIS data preview on hover
- Keyboard navigation

**Implementation**:
```typescript
'use client';

import { useState, useEffect, useRef } from 'react';
import { Search } from 'lucide-react';
import type { ParcelAnalysis } from '@/lib/arcgis-client';

interface ParcelAutocompleteProps {
  onParcelSelected: (analysis: ParcelAnalysis) => void;
  placeholder?: string;
}

export default function ParcelAutocomplete({
  onParcelSelected,
  placeholder = "Search by APN (e.g., 4289-005-004)"
}: ParcelAutocompleteProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [suggestions, setSuggestions] = useState<ParcelAnalysis[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);

  // Debounced search
  useEffect(() => {
    if (searchTerm.length < 3) {
      setSuggestions([]);
      return;
    }

    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const response = await fetch(
          `/autocomplete/parcels?q=${encodeURIComponent(searchTerm)}&limit=10`
        );
        const data = await response.json();
        setSuggestions(data.suggestions || []);
      } catch (error) {
        console.error('Autocomplete error:', error);
        setSuggestions([]);
      } finally {
        setIsSearching(false);
      }
    }, 300);  // 300ms debounce

    return () => clearTimeout(timer);
  }, [searchTerm]);

  // Keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => Math.min(prev + 1, suggestions.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => Math.max(prev - 1, -1));
    } else if (e.key === 'Enter' && selectedIndex >= 0) {
      e.preventDefault();
      handleSelect(suggestions[selectedIndex]);
    }
  };

  const handleSelect = (analysis: ParcelAnalysis) => {
    setSearchTerm(analysis.parcel.apn);
    setSuggestions([]);
    setSelectedIndex(-1);
    onParcelSelected(analysis);
  };

  return (
    <div className="relative">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          ref={inputRef}
          type="text"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
        />
      </div>

      {/* Suggestions dropdown */}
      {suggestions.length > 0 && (
        <div className="absolute z-[2000] w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-96 overflow-y-auto">
          {suggestions.map((suggestion, index) => (
            <button
              key={suggestion.parcel.apn}
              onClick={() => handleSelect(suggestion)}
              className={`w-full px-4 py-3 text-left hover:bg-gray-50 transition-colors border-b border-gray-100 last:border-b-0 ${
                index === selectedIndex ? 'bg-blue-50' : ''
              }`}
            >
              <div className="font-semibold text-gray-900">{suggestion.parcel.apn}</div>
              <div className="text-sm text-gray-600 mt-1">{suggestion.parcel.situsFullAddress}</div>
              <div className="text-xs text-gray-500 mt-1">
                {suggestion.zoning.zoneCode} • {suggestion.parcel.lotSizeSqft?.toLocaleString()} sq ft
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Loading indicator */}
      {isSearching && (
        <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
          <svg className="animate-spin h-4 w-4 text-gray-400" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        </div>
      )}
    </div>
  );
}
```

### ResultsDashboard.tsx

**Purpose**: Display analysis results with scenario comparison and recommendations.

**Key Features**:
- Tabbed interface (Overview, Scenarios, Constraints)
- Scenario comparison cards
- Recommended scenario highlighting
- Downloadable reports

**Structure**:
```typescript
export default function ResultsDashboard({
  analysis,
  onReset
}: {
  analysis: AnalysisResponse;
  onReset: () => void;
}) {
  const [activeTab, setActiveTab] = useState<'overview' | 'scenarios' | 'constraints'>('overview');

  return (
    <div className="space-y-6">
      {/* Header with reset button */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Analysis Results</h2>
          <p className="text-gray-600 mt-1">Parcel: {analysis.parcel_apn}</p>
        </div>
        <button
          onClick={onReset}
          className="px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          New Analysis
        </button>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-4">
          {['overview', 'scenarios', 'constraints'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as any)}
              className={`px-4 py-2 border-b-2 font-medium transition-colors ${
                activeTab === tab
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab content */}
      {activeTab === 'overview' && (
        <OverviewTab
          baseScenario={analysis.base_scenario}
          recommendedScenario={analysis.recommended_scenario}
          applicableLaws={analysis.applicable_laws}
        />
      )}

      {activeTab === 'scenarios' && (
        <ScenariosTab
          baseScenario={analysis.base_scenario}
          alternativeScenarios={analysis.alternative_scenarios}
          recommendedScenario={analysis.recommended_scenario}
        />
      )}

      {activeTab === 'constraints' && (
        <ConstraintsTab warnings={analysis.warnings} />
      )}
    </div>
  );
}
```

### ScenarioComparison.tsx

**Purpose**: Side-by-side scenario comparison cards.

**Card Pattern**:
```typescript
function ScenarioCard({ scenario, isRecommended }: {
  scenario: DevelopmentScenario;
  isRecommended: boolean;
}) {
  return (
    <div className={`bg-white rounded-lg border p-6 ${
      isRecommended ? 'border-blue-500 ring-2 ring-blue-200' : 'border-gray-200'
    }`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">
            {scenario.scenario_name}
          </h3>
          <p className="text-sm text-gray-600 mt-1">{scenario.legal_basis}</p>
        </div>
        {isRecommended && (
          <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded">
            Recommended
          </span>
        )}
      </div>

      {/* Key metrics */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <MetricItem label="Max Units" value={scenario.max_units} />
        <MetricItem label="Max Height" value={`${scenario.max_height_ft} ft`} />
        <MetricItem label="Building Size" value={`${scenario.max_building_sqft.toLocaleString()} sq ft`} />
        <MetricItem label="Parking" value={`${scenario.parking_spaces_required} spaces`} />
      </div>

      {/* Affordable units */}
      {scenario.affordable_units_required > 0 && (
        <div className="p-3 bg-green-50 border border-green-200 rounded-lg mb-4">
          <div className="text-sm font-medium text-green-900">
            Affordable Units Required: {scenario.affordable_units_required}
          </div>
        </div>
      )}

      {/* Notes */}
      <details className="text-sm">
        <summary className="cursor-pointer text-blue-600 hover:text-blue-700 font-medium">
          View Details
        </summary>
        <ul className="mt-2 space-y-1 text-gray-700">
          {scenario.notes.map((note, index) => (
            <li key={index} className="pl-4">
              {note}
            </li>
          ))}
        </ul>
      </details>
    </div>
  );
}
```

## Tailwind CSS Patterns

### Cards

```typescript
// Standard card
className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"

// Highlighted card
className="bg-white rounded-lg border-2 border-blue-500 p-6 ring-2 ring-blue-200"

// Colored background card
className="p-3 bg-blue-50 border border-blue-200 rounded-lg"
```

### Buttons

```typescript
// Primary button
className="px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"

// Secondary button
className="px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors font-medium"

// Danger button
className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"

// Toggle button (active/inactive)
className={`px-4 py-2 rounded-lg font-medium transition-colors ${
  isActive
    ? 'bg-blue-600 text-white'
    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
}`}
```

### Alerts

```typescript
// Error alert
<div className="mb-6 bg-red-50 border-l-4 border-red-500 rounded-lg p-4">
  <div className="flex items-start gap-3">
    <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
    <div>
      <h3 className="font-semibold text-red-900 mb-1">Error Title</h3>
      <p className="text-red-800 text-sm">Error message</p>
    </div>
  </div>
</div>

// Warning alert
<div className="flex items-start gap-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
  <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
  <div className="flex-1">
    <span className="text-sm font-medium text-amber-900">Warning</span>
    <p className="text-xs text-amber-700 mt-1">Warning message</p>
  </div>
</div>

// Info alert
<div className="flex items-start gap-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
  <AlertCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
  <div className="flex-1">
    <span className="text-sm font-medium text-blue-900">Information</span>
    <p className="text-xs text-blue-700 mt-1">Info message</p>
  </div>
</div>

// Success alert
<div className="flex items-start gap-3 p-3 bg-green-50 border border-green-200 rounded-lg">
  <AlertCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
  <div className="flex-1">
    <span className="text-sm font-medium text-green-900">Success</span>
    <p className="text-xs text-green-700 mt-1">Success message</p>
  </div>
</div>
```

### Grids and Layout

```typescript
// Two-column grid
className="grid grid-cols-1 md:grid-cols-2 gap-6"

// Three-column grid
className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"

// Container
className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8"

// Responsive flex
className="flex flex-col md:flex-row gap-4 items-center"
```

## Accessibility

### ARIA Labels

```typescript
<button
  aria-label="Reset analysis"
  onClick={handleReset}
>
  <X className="w-5 h-5" />
</button>

<input
  aria-label="Assessor Parcel Number"
  aria-describedby="apn-help"
  type="text"
  id="apn"
/>
<p id="apn-help" className="text-xs text-gray-500">
  Format: 1234-567-890
</p>
```

### Keyboard Navigation

```typescript
// Ensure focusable elements are keyboard accessible
<button
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  }}
  className="focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
>
  Click me
</button>
```

## Related Documentation

- [Frontend CLAUDE.md](../CLAUDE.md) - Overall frontend patterns
- [Root CLAUDE.md](../../CLAUDE.md) - Project overview
- [Backend CLAUDE.md](../../app/CLAUDE.md) - API integration
