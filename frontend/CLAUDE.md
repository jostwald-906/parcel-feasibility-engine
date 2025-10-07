# Frontend (Next.js) - AI Agent Context

## Overview

Next.js 15.5.4 frontend with TypeScript, Turbopack, Tailwind CSS v4, and React-Leaflet for interactive parcel analysis and mapping.

**Key Features**:
- Interactive map-based parcel selection
- Form-based manual parcel entry
- APN autocomplete with GIS integration
- Real-time development scenario comparison
- Responsive design with Tailwind CSS v4

## Technology Stack

- **Next.js 15.5.4** with App Router
- **TypeScript 5**
- **Turbopack** (dev and build)
- **React 19.1.0** + React DOM 19.1.0
- **Tailwind CSS v4** with @tailwindcss/postcss
- **React-Leaflet 5.0.0** + Leaflet 1.9.4
- **Axios 1.12.2** for API calls
- **Lucide React** 0.544.0 for icons
- **Recharts** 3.2.1 for charts
- **Testing**: Jest 29.7.0, Testing Library

## Directory Structure

```
frontend/
├── app/                        # Next.js App Router
│   ├── page.tsx                # Main application page
│   ├── layout.tsx              # Root layout
│   ├── globals.css             # Global styles (Tailwind)
│   └── favicon.ico
├── components/                 # React components
│   ├── ParcelForm.tsx          # Main analysis form
│   ├── ParcelMap.tsx           # Leaflet map component
│   ├── ParcelMapWrapper.tsx    # Client-side map wrapper
│   ├── ParcelInfoPanel.tsx     # GIS data display panel
│   ├── ParcelAutocomplete.tsx  # APN search/autocomplete
│   ├── MultiParcelSelector.tsx # Multiple parcel selection
│   ├── ProposedProjectForm.tsx # Proposed project details
│   ├── ResultsDashboard.tsx    # Analysis results display
│   ├── ScenarioComparison.tsx  # Scenario comparison cards
│   ├── CNELDisplayCard.tsx     # Noise analysis display
│   ├── CommunityBenefitsCard.tsx # Community benefits
│   └── OverlayDetailCard.tsx   # Overlay zone details
├── lib/                        # Utilities and clients
│   ├── api.ts                  # Backend API client (Axios)
│   ├── types.ts                # TypeScript type definitions
│   ├── arcgis-client.ts        # ArcGIS REST API client
│   ├── parcel-combiner.ts      # Multi-parcel combination logic
│   └── constants/
│       └── zoning-codes.ts     # Santa Monica zoning codes
├── public/                     # Static assets
├── package.json                # Dependencies and scripts
├── tsconfig.json               # TypeScript configuration
└── tailwind.config.ts          # Tailwind CSS v4 config
```

## Development Setup

```bash
# From frontend/ directory

# Install dependencies
npm install

# Run development server with Turbopack
npm run dev
```

Frontend runs at: http://localhost:3000

## Development Commands

```bash
# Development server (Turbopack)
npm run dev

# Production build
npm run build

# Run production build locally
npm start

# Lint
npm run lint

# Type check
npm run type-check

# Run tests
npm test

# Run tests in watch mode
npm run test:watch

# Coverage report
npm run test:coverage
```

## Environment Variables

Create `.env.local` in frontend/ directory:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Important**: All public environment variables must be prefixed with `NEXT_PUBLIC_`.

Access in code:
```typescript
const apiUrl = process.env.NEXT_PUBLIC_API_URL;
```

## TypeScript Types (lib/types.ts)

All types mirror backend Pydantic models with snake_case field names.

### Core Types

```typescript
export interface Parcel {
  apn: string;
  address: string;
  city: string;
  county: string;
  zip_code: string;
  lot_size_sqft: number;
  lot_width_ft?: number;
  lot_depth_ft?: number;
  zoning_code: string;
  general_plan?: string;
  existing_units: number;
  existing_building_sqft: number;
  year_built?: number;
  latitude?: number;
  longitude?: number;

  // Current use information
  use_code?: string;
  use_type?: string;          // e.g., "Residential", "Commercial"
  use_description?: string;   // e.g., "Single Family Residence"

  // Density Bonus fields
  for_sale?: boolean;
  avg_bedrooms_per_unit?: number;
  near_transit?: boolean;
  street_row_width?: number;

  // Tier and overlay
  development_tier?: string;
  overlay_codes?: string[];

  // Environmental flags
  in_coastal_zone?: boolean;
  in_flood_zone?: boolean;
  is_historic_property?: boolean;
  in_wetlands?: boolean;
  in_conservation_area?: boolean;
  fire_hazard_zone?: string | null;
  near_hazardous_waste?: boolean;
  in_earthquake_fault_zone?: boolean;
}

export interface AnalysisRequest {
  parcel: Parcel;
  proposed_project?: ProposedProject;
  include_sb9?: boolean;
  include_sb35?: boolean;
  include_ab2011?: boolean;
  include_density_bonus?: boolean;
  target_affordability_pct?: number;
}

export interface DevelopmentScenario {
  scenario_name: string;
  legal_basis: string;
  max_units: number;
  max_building_sqft: number;
  max_height_ft: number;
  max_stories: number;
  parking_spaces_required: number;
  affordable_units_required: number;
  setbacks: {
    front?: number;
    rear?: number;
    side?: number;
  };
  lot_coverage_pct: number;
  estimated_buildable_sqft?: number;
  notes: string[];
}

export interface AnalysisResponse {
  parcel_apn: string;
  analysis_date: string;
  base_scenario: DevelopmentScenario;
  alternative_scenarios: DevelopmentScenario[];
  recommended_scenario: string;
  recommendation_reason: string;
  applicable_laws: string[];
  potential_incentives: string[];
  warnings?: string[];
  rent_control?: RentControlData;
}
```

### Optional Fields Convention

Use `?` for all optional fields:

```typescript
year_built?: number;          // May not exist
use_type?: string;            // May be null from GIS
overlay_codes?: string[];     // May be undefined
```

## Component Patterns

### Client Components

All interactive components must use `'use client'` directive:

```typescript
'use client';

import { useState } from 'react';

export default function ParcelForm() {
  const [formData, setFormData] = useState({...});
  // ...
}
```

### Form Input Pattern (CRITICAL)

**ALL text inputs MUST use `text-gray-900` className** to ensure text is visible:

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

**Why**: Default Tailwind text color is white, which is invisible on white backgrounds.

### Select Pattern

```typescript
<select
  name="zoning_code"
  value={formData.zoning_code}
  onChange={handleInputChange}
  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900"
  required
>
  <option value="R1">R1 - Single Family</option>
  <option value="R2">R2 - Low Density Multi-Family</option>
</select>
```

### Tailwind CSS v4 Patterns

```typescript
// Container
className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8"

// Card
className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"

// Button (primary)
className="px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"

// Button (secondary)
className="px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"

// Alert (error)
className="mb-6 bg-red-50 border-l-4 border-red-500 rounded-lg p-4"

// Alert (warning)
className="flex items-start gap-3 p-3 bg-amber-50 border border-amber-200 rounded-lg"

// Alert (info)
className="flex items-start gap-3 p-3 bg-blue-50 border border-blue-200 rounded-lg"
```

### Icons (Lucide React)

```typescript
import { Building2, AlertCircle, Map, Layers } from 'lucide-react';

// In component
<Building2 className="w-5 h-5 text-blue-600" />
<AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
```

## API Integration (lib/api.ts)

### API Client

```typescript
import axios from 'axios';
import type { AnalysisRequest, AnalysisResponse } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,  // 30 seconds
});

const ParcelAPI = {
  async analyzeParcel(request: AnalysisRequest): Promise<AnalysisResponse> {
    const response = await apiClient.post<AnalysisResponse>(
      '/api/v1/analyze',
      request
    );
    return response.data;
  },

  async healthCheck(): Promise<any> {
    const response = await apiClient.get('/health');
    return response.data;
  },
};

export default ParcelAPI;
```

### Error Handling

```typescript
const handleAnalyze = async (request: AnalysisRequest) => {
  setIsLoading(true);
  setError(null);

  try {
    const result = await ParcelAPI.analyzeParcel(request);
    setAnalysisResult(result);
  } catch (err) {
    console.error('Analysis error:', err);

    // Extract error message from various error formats
    const errorMessage =
      (err && typeof err === 'object' && 'response' in err &&
       err.response && typeof err.response === 'object' &&
       'data' in err.response && err.response.data &&
       typeof err.response.data === 'object' && 'detail' in err.response.data)
        ? String(err.response.data.detail)
        : (err instanceof Error ? err.message : null) ||
          'Failed to analyze parcel. Please check your inputs and try again.';

    setError(errorMessage);
  } finally {
    setIsLoading(false);
  }
};
```

## Map Integration (React-Leaflet)

### Map Wrapper Pattern

Leaflet requires client-side rendering. Use dynamic import:

```typescript
// components/ParcelMapWrapper.tsx
'use client';

import dynamic from 'next/dynamic';

const ParcelMap = dynamic(() => import('./ParcelMap'), {
  ssr: false,  // CRITICAL: Disable server-side rendering
  loading: () => <div>Loading map...</div>
});

export default function ParcelMapWrapper({ onParcelSelected, height }) {
  return <ParcelMap onParcelSelected={onParcelSelected} height={height} />;
}
```

### Map Component

```typescript
// components/ParcelMap.tsx
'use client';

import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

export default function ParcelMap({ onParcelSelected, height = "500px" }) {
  return (
    <MapContainer
      center={[34.0195, -118.4912]}  // Santa Monica
      zoom={13}
      style={{ height, width: '100%' }}
      className="rounded-lg"
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; OpenStreetMap contributors'
      />
      {/* Add custom layers, markers, polygons */}
    </MapContainer>
  );
}
```

### Z-Index for Map Overlays

**CRITICAL**: Custom overlays must use `z-[1000]` or higher to appear above map tiles:

```typescript
// Parcel boundary overlay
<div className="absolute top-0 left-0 w-full h-full z-[1000] pointer-events-none">
  {/* Custom overlay content */}
</div>

// Leaflet pane configuration
const pane = map.createPane('parcels');
pane.style.zIndex = '1000';
```

## GIS Data Conventions

### Field Names

GIS field names are **lowercase**:

```typescript
// CORRECT
interface GISParcel {
  usetype: string;          // "Residential"
  usedescription: string;   // "Single Family Residence"
  usecode: string;          // "0100"
}

// WRONG
interface GISParcel {
  UseType: string;       // ❌ Wrong case
  UseDescription: string; // ❌ Wrong case
}
```

### Optional GIS Fields

Always use optional types for GIS data:

```typescript
interface ParcelAnalysis {
  parcel: {
    useType?: string;           // May not exist in all data sources
    useDescription?: string;    // May be null
    useCode?: string;           // May be undefined
    yearBuilt?: string;         // String from GIS, convert to number
    units?: number;             // May be null
  };
}
```

### Current Use Display

Always include useType, useDescription alongside useCode:

```typescript
{(initialData?.parcel?.useType || initialData?.parcel?.useDescription) && (
  <div className="mb-4 p-3 bg-gray-50 border border-gray-200 rounded-lg">
    <div className="text-xs font-semibold text-gray-600 mb-1">Current Use</div>
    {initialData.parcel.useType && (
      <div className="text-sm font-semibold text-gray-900">
        {initialData.parcel.useType}
      </div>
    )}
    {initialData.parcel.useDescription && (
      <div className="text-sm text-gray-700 mt-0.5">
        {initialData.parcel.useDescription}
      </div>
    )}
  </div>
)}
```

## State Management

### Component State

Use `useState` for component-local state:

```typescript
const [formData, setFormData] = useState<Partial<Parcel>>({
  apn: '',
  address: '',
  city: 'Santa Monica',
  // ...
});

const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
const [isLoading, setIsLoading] = useState(false);
const [error, setError] = useState<string | null>(null);
```

### Lifting State

Pass state and setters through props:

```typescript
// Parent
const [selectedParcel, setSelectedParcel] = useState<ParcelAnalysis | null>(null);

<ParcelMap onParcelSelected={setSelectedParcel} />

// Child
interface ParcelMapProps {
  onParcelSelected: (parcel: ParcelAnalysis) => void;
}
```

## Form Handling Patterns

### Input Change Handler

```typescript
const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
  const { name, value, type } = e.target;

  // Parse numbers
  const parsedValue = type === 'number'
    ? (value === '' ? undefined : parseFloat(value))
    : value;

  setFormData(prev => ({
    ...prev,
    [name]: parsedValue,
  }));
};
```

### Checkbox Handler

```typescript
const handleOptionChange = (e: React.ChangeEvent<HTMLInputElement>) => {
  const { name, type, checked, value } = e.target;

  setOptions(prev => ({
    ...prev,
    [name]: type === 'checkbox' ? checked : parseFloat(value),
  }));
};
```

### Form Submit

```typescript
const handleSubmit = (e: React.FormEvent) => {
  e.preventDefault();

  // Validation
  if (!formData.apn || !formData.address || !formData.lot_size_sqft) {
    alert('Please fill in all required fields');
    return;
  }

  // Build request
  const request: AnalysisRequest = {
    parcel: formData as Parcel,
    proposed_project: proposedProject,
    include_sb9: options.include_sb9,
    include_sb35: options.include_sb35,
    include_ab2011: options.include_ab2011,
    include_density_bonus: options.include_density_bonus,
    target_affordability_pct: options.target_affordability_pct,
  };

  onSubmit(request);
};
```

## Autocomplete Pattern

```typescript
// components/ParcelAutocomplete.tsx

const [searchTerm, setSearchTerm] = useState('');
const [suggestions, setSuggestions] = useState<ParcelAnalysis[]>([]);
const [isSearching, setIsSearching] = useState(false);

// Debounced search
useEffect(() => {
  if (searchTerm.length < 3) {
    setSuggestions([]);
    return;
  }

  const timer = setTimeout(async () => {
    setIsSearching(true);
    try {
      const results = await searchParcels(searchTerm);
      setSuggestions(results);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setIsSearching(false);
    }
  }, 300);  // 300ms debounce

  return () => clearTimeout(timer);
}, [searchTerm]);
```

## Loading States

```typescript
{isLoading ? (
  <span className="flex items-center gap-2">
    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
        fill="none"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
    Analyzing...
  </span>
) : (
  'Analyze Development Potential'
)}
```

## Conditional Rendering

```typescript
// Render if data exists
{analysisResult && (
  <ResultsDashboard analysis={analysisResult} onReset={handleReset} />
)}

// Render with fallback
{selectedParcelData ? (
  <ParcelInfoPanel analysis={selectedParcelData} />
) : (
  <div className="text-gray-500">Select a parcel to view details</div>
)}

// Conditional classes
className={`px-4 py-2 rounded-lg font-medium transition-colors ${
  isActive
    ? 'bg-blue-600 text-white'
    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
}`}
```

## Testing

### Component Tests

```typescript
// __tests__/ParcelForm.test.tsx

import { render, screen, fireEvent } from '@testing-library/react';
import ParcelForm from '@/components/ParcelForm';

describe('ParcelForm', () => {
  it('renders form fields', () => {
    render(<ParcelForm onSubmit={jest.fn()} />);

    expect(screen.getByLabelText(/APN/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Address/i)).toBeInTheDocument();
  });

  it('submits form with valid data', () => {
    const handleSubmit = jest.fn();
    render(<ParcelForm onSubmit={handleSubmit} />);

    fireEvent.change(screen.getByLabelText(/APN/i), {
      target: { value: '123-456-789' }
    });

    fireEvent.click(screen.getByText(/Analyze/i));

    expect(handleSubmit).toHaveBeenCalled();
  });
});
```

## Common Issues and Solutions

### Issue: White text in inputs
**Solution**: Add `text-gray-900` to all input/select elements

### Issue: Map not rendering
**Solution**: Ensure dynamic import with `ssr: false`, check Leaflet CSS import

### Issue: Map overlays hidden
**Solution**: Use `z-[1000]` or higher z-index

### Issue: GIS field not found
**Solution**: Check field name is lowercase (usetype not UseType)

### Issue: Type errors with optional fields
**Solution**: Use optional chaining `parcel?.useType` or nullish coalescing `parcel.useType ?? 'Unknown'`

### Issue: CORS errors
**Solution**: Verify NEXT_PUBLIC_API_URL points to backend with correct CORS settings

## Deployment (Vercel)

```bash
# From frontend/ directory

# Install Vercel CLI
npm install -g vercel

# Login
vercel login

# Deploy
vercel

# Deploy to production
vercel --prod
```

Set environment variables in Vercel dashboard:
- `NEXT_PUBLIC_API_URL`: Your backend URL (Railway)

## Related Documentation

- [Root CLAUDE.md](../CLAUDE.md) - Overall project
- [Components CLAUDE.md](components/CLAUDE.md) - Component patterns
- [Backend CLAUDE.md](../app/CLAUDE.md) - API integration
