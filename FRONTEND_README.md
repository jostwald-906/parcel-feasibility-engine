# Santa Monica Parcel Feasibility Engine - Frontend Dashboard

**Professional React/Next.js Dashboard for Parcel Analysis**

---

## 🎯 Overview

A modern, responsive web dashboard built with **Next.js 15**, **TypeScript**, **Tailwind CSS**, and **Recharts** that provides an intuitive interface for analyzing parcel development feasibility.

---

## ✨ Features

### 1. **Interactive Parcel Input Form**
- Comprehensive form with validation
- Pre-configured California zoning codes (R1, R2, R3, R4, C-1, C-2, C-3)
- Analysis options for state housing laws:
  - ✅ SB 9 (2021) - Lot splits and duplexes
  - ✅ SB 35 (2017) - Streamlined approval
  - ✅ AB 2011 (2022) - Commercial conversions
  - ✅ Density Bonus Law with affordability targeting

### 2. **Results Dashboard**
- **Key Metrics Cards:**
  - Base units allowed
  - Maximum units possible
  - State laws applicable
  - Scenarios analyzed

- **Visual Charts:**
  - Unit comparison bar chart
  - Building size comparisons
  - Interactive with Recharts

- **Recommendation Engine:**
  - Highlighted recommended scenario
  - Clear explanation of benefits

### 3. **Scenario Comparison Table**
- Side-by-side comparison of all scenarios
- Color-coded recommended option
- Detailed metrics:
  - Legal basis
  - Max units
  - Max building size
  - Height & stories
  - Parking requirements
  - Affordable units
  - Setbacks
  - Lot coverage

### 4. **State Law Information**
- Applicable laws badge display
- Potential incentives list
- Warnings and considerations

---

## 🏗️ Tech Stack

- **Framework:** Next.js 15.5.4 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Icons:** Lucide React
- **Charts:** Recharts
- **HTTP Client:** Axios
- **UI Components:** Headless UI
- **Build Tool:** Turbopack

---

## 📁 Project Structure

```
frontend/
├── app/
│   ├── page.tsx              # Main application page
│   ├── layout.tsx            # Root layout
│   └── globals.css           # Global styles
├── components/
│   ├── ParcelForm.tsx        # Input form component
│   ├── ResultsDashboard.tsx  # Results display
│   └── ScenarioComparison.tsx # Comparison table
├── lib/
│   ├── api.ts                # API client
│   ├── types.ts              # TypeScript types
│   └── utils.ts              # Utility functions
├── .env.local                # Environment variables
└── package.json              # Dependencies
```

---

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ installed
- Backend API running on http://localhost:8000

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

The dashboard will be available at **http://localhost:3001**

### Production Build

```bash
npm run build
npm start
```

---

## 🔗 API Integration

The frontend connects to the backend API via the `ParcelAPI` client in [lib/api.ts](lib/api.ts).

### Environment Variables

Create `.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### API Methods

- `ParcelAPI.healthCheck()` - Check API status
- `ParcelAPI.analyzeParcel(request)` - Full parcel analysis
- `ParcelAPI.quickAnalysis(request)` - Quick metrics only
- `ParcelAPI.getStateLawInfo(lawCode)` - State law details
- `ParcelAPI.getAllStateLaws()` - All laws at once

---

## 📸 UI Components

### ParcelForm
Collects parcel data with sections:
- Parcel Information (APN, zoning)
- Location (address, city, coordinates)
- Dimensions (lot size, width, depth)
- Existing Development (units, building size, year built)
- Analysis Options (state law toggles, affordability target)

### ResultsDashboard
Displays analysis results:
- Header with reset button
- Key metrics cards with icons
- Recommendation badge
- Warnings section
- Unit comparison chart
- Applicable laws grid
- Potential incentives list

### ScenarioComparison
Interactive comparison table:
- Sticky header with recommended tag
- Metrics rows with icons
- Hover effects
- Scenario details cards with notes

---

## 🎨 Design System

### Colors
- **Primary Blue:** `#3b82f6` (Blue-600)
- **Success Green:** `#10b981` (Green-600)
- **Warning Yellow:** `#f59e0b` (Yellow-500)
- **Error Red:** `#ef4444` (Red-500)

### Typography
- **Font:** Geist Sans (Variable)
- **Mono:** Geist Mono (Variable)

### Spacing
- Consistent 4px grid system
- Tailwind spacing scale

---

## 🧪 Testing the Integration

### 1. Start Backend API
```bash
cd "/Users/Jordan_Ostwald/Parcel Feasibility Engine"
docker-compose up -d
```

### 2. Start Frontend
```bash
cd frontend
npm run dev
```

### 3. Test Analysis

**Example Input:**
- APN: 4276-019-030
- Address: 123 Main Street
- City: Santa Monica
- ZIP: 90401
- Lot Size: 5,000 sq ft
- Zoning: R1
- Existing Units: 1
- Existing Building: 1,800 sq ft
- Year Built: 1955

**Expected Output:**
- Base scenario: 1 unit
- SB9 Duplex: 2 units (+100%)
- SB9 Lot Split: 4 units (+300%)
- SB35 Streamlined: 2 units
- Recommended: SB9 Lot Split

---

## 📊 Features Demonstrated

### ✅ Form Validation
- Required fields marked with *
- Type validation (numbers, text)
- Range validation (affordability 0-100%)

### ✅ Responsive Design
- Mobile-first approach
- Tablet breakpoints (md:)
- Desktop layouts (lg:)

### ✅ Loading States
- Button disabled during analysis
- Loading text feedback

### ✅ Error Handling
- API error display
- User-friendly messages
- Retry capability

### ✅ Accessibility
- Semantic HTML
- ARIA labels
- Keyboard navigation
- Focus states

---

## 🔧 Customization

### Adding New Zoning Codes

Edit [components/ParcelForm.tsx](components/ParcelForm.tsx):

```tsx
<option value="NEW-ZONE">NEW-ZONE - Description</option>
```

### Changing API URL

Update `.env.local`:

```bash
NEXT_PUBLIC_API_URL=https://api.example.com
```

### Customizing Colors

Edit [tailwind.config.ts](tailwind.config.ts) or use Tailwind classes directly.

---

## 🐛 Troubleshooting

### Port 3001 Already in Use

```bash
PORT=3002 npm run dev
```

### API Connection Error

1. Verify backend is running: `curl http://localhost:8000/health`
2. Check CORS settings in backend
3. Verify `.env.local` has correct URL

### Build Errors

```bash
rm -rf .next node_modules
npm install
npm run dev
```

---

## 📚 Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS](https://tailwindcss.com/docs)
- [Recharts](https://recharts.org/en-US/api)
- [TypeScript](https://www.typescriptlang.org/docs)

---

## 🎯 Next Steps

### High Priority
1. Add PDF export functionality
2. Implement map visualization with parcel location
3. Add save/load analysis feature
4. Create print-friendly view

### Medium Priority
5. Add comparison mode (multiple parcels)
6. Implement dark mode
7. Add keyboard shortcuts
8. Create shareable analysis links

### Low Priority
9. Add animation transitions
10. Implement data caching
11. Add analytics tracking
12. Create guided tour

---

## 📝 License

Part of the Santa Monica Parcel Feasibility Engine project.

---

## 🤝 Contributing

When making changes:
1. Follow TypeScript strict mode
2. Use Tailwind utility classes
3. Maintain component modularity
4. Add proper error handling

---

*Built with ❤️ using Next.js, TypeScript, and Tailwind CSS*
