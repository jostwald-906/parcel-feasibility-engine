#!/usr/bin/env ts-node
/**
 * ArcGIS Endpoint Validation Script
 *
 * Verifies that all discovered service endpoints are accessible and
 * validates their metadata (layer names, geometry types, field schemas).
 *
 * Usage: npx tsx scripts/verify-endpoints.ts
 */

import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

interface ServiceEndpoint {
  url: string;
  layerName?: string;
  layerId?: number;
  geometryType?: string;
  fields?: Record<string, string>;
  keyFields?: string[];
}

interface ConnectionManifest {
  parcels?: ServiceEndpoint;
  zoning?: ServiceEndpoint;
  historic?: ServiceEndpoint;
  coastal?: ServiceEndpoint;
  flood?: ServiceEndpoint;
  transit?: ServiceEndpoint;
  parking?: ServiceEndpoint;
  setbacks?: ServiceEndpoint;
  overlays?: ServiceEndpoint[];
  hazards?: ServiceEndpoint[];
}

interface ValidationResult {
  url: string;
  status: 'success' | 'failed' | 'warning';
  accessible: boolean;
  layerName?: string;
  geometryType?: string;
  fieldCount?: number;
  sampleFeatures?: number;
  errors?: string[];
  warnings?: string[];
}

/**
 * Fetch JSON from ArcGIS endpoint
 */
async function fetchJSON(url: string): Promise<any> {
  try {
    const response = await fetch(`${url}?f=json`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`Failed to fetch ${url}:`, error);
    return null;
  }
}

/**
 * Validate a single service endpoint
 */
async function validateEndpoint(endpoint: ServiceEndpoint): Promise<ValidationResult> {
  const result: ValidationResult = {
    url: endpoint.url,
    status: 'success',
    accessible: false,
    errors: [],
    warnings: [],
  };

  // 1. Check if endpoint is accessible
  const metadata = await fetchJSON(endpoint.url);

  if (!metadata) {
    result.status = 'failed';
    result.errors!.push('Endpoint not accessible');
    return result;
  }

  if (metadata.error) {
    result.status = 'failed';
    result.errors!.push(`Service error: ${metadata.error.message}`);
    return result;
  }

  result.accessible = true;

  // 2. Validate layer metadata
  result.layerName = metadata.name || metadata.displayFieldName;
  result.geometryType = metadata.geometryType;
  result.fieldCount = metadata.fields?.length || 0;

  if (!result.geometryType) {
    result.warnings!.push('No geometry type specified');
  }

  if (!metadata.fields || metadata.fields.length === 0) {
    result.warnings!.push('No fields defined');
  }

  // 3. Verify expected fields exist
  if (endpoint.fields && metadata.fields) {
    const actualFieldNames = new Set(
      metadata.fields.map((f: any) => f.name.toLowerCase())
    );

    const expectedFields = Object.keys(endpoint.fields);
    const missingFields = expectedFields.filter(
      (field) => !actualFieldNames.has(field.toLowerCase())
    );

    if (missingFields.length > 0) {
      result.warnings!.push(`Missing expected fields: ${missingFields.join(', ')}`);
    }
  }

  // 4. Test query with sample feature
  try {
    const queryUrl = `${endpoint.url}/query`;
    const queryParams = new URLSearchParams({
      where: '1=1',
      outFields: '*',
      returnGeometry: 'false',
      resultRecordCount: '1',
      f: 'json',
    });

    const queryResponse = await fetch(`${queryUrl}?${queryParams.toString()}`);
    const queryData = await queryResponse.json();

    if (queryData.features && queryData.features.length > 0) {
      result.sampleFeatures = queryData.features.length;

      // Log sample attributes
      const sampleAttrs = queryData.features[0].attributes;
      console.log(`   Sample attributes:`, Object.keys(sampleAttrs).slice(0, 5).join(', '), '...');
    } else {
      result.warnings!.push('No features returned from sample query');
    }
  } catch (error) {
    result.warnings!.push(`Query test failed: ${error}`);
  }

  // 5. Set final status
  if (result.errors!.length > 0) {
    result.status = 'failed';
  } else if (result.warnings!.length > 0) {
    result.status = 'warning';
  }

  return result;
}

/**
 * Validate all endpoints in manifest
 */
async function validateManifest(manifest: ConnectionManifest): Promise<ValidationResult[]> {
  const results: ValidationResult[] = [];

  // Validate single endpoints
  const singleEndpoints: Array<[string, ServiceEndpoint | undefined]> = [
    ['Parcels', manifest.parcels],
    ['Zoning', manifest.zoning],
    ['Historic', manifest.historic],
    ['Coastal', manifest.coastal],
    ['Flood', manifest.flood],
    ['Transit', manifest.transit],
    ['Parking', manifest.parking],
    ['Setbacks', manifest.setbacks],
  ];

  for (const [name, endpoint] of singleEndpoints) {
    if (endpoint) {
      console.log(`\n🔍 Validating ${name}...`);
      const result = await validateEndpoint(endpoint);
      results.push(result);
      logResult(name, result);
    }
  }

  // Validate overlay arrays
  if (manifest.overlays && manifest.overlays.length > 0) {
    console.log(`\n🔍 Validating ${manifest.overlays.length} Overlays...`);
    for (const [index, overlay] of manifest.overlays.entries()) {
      console.log(`   [${index + 1}/${manifest.overlays.length}] ${overlay.layerName || 'Unnamed'}`);
      const result = await validateEndpoint(overlay);
      results.push(result);
      if (result.status === 'failed') {
        console.log(`   ❌ ${result.errors?.join(', ')}`);
      }
    }
  }

  // Validate hazard arrays
  if (manifest.hazards && manifest.hazards.length > 0) {
    console.log(`\n🔍 Validating ${manifest.hazards.length} Hazards...`);
    for (const [index, hazard] of manifest.hazards.entries()) {
      console.log(`   [${index + 1}/${manifest.hazards.length}] ${hazard.layerName || 'Unnamed'}`);
      const result = await validateEndpoint(hazard);
      results.push(result);
      if (result.status === 'failed') {
        console.log(`   ❌ ${result.errors?.join(', ')}`);
      }
    }
  }

  return results;
}

/**
 * Log validation result
 */
function logResult(name: string, result: ValidationResult): void {
  if (result.status === 'success') {
    console.log(`   ✅ ${name} - ${result.layerName} (${result.geometryType})`);
    console.log(`      Fields: ${result.fieldCount}, Sample features: ${result.sampleFeatures}`);
  } else if (result.status === 'warning') {
    console.log(`   ⚠️  ${name} - ${result.layerName || 'Unknown'}`);
    result.warnings?.forEach((w) => console.log(`      Warning: ${w}`));
  } else {
    console.log(`   ❌ ${name} - FAILED`);
    result.errors?.forEach((e) => console.log(`      Error: ${e}`));
  }
}

/**
 * Generate summary report
 */
function generateSummary(results: ValidationResult[]): void {
  console.log('\n' + '='.repeat(80));
  console.log('📊 VALIDATION SUMMARY\n');

  const successful = results.filter((r) => r.status === 'success').length;
  const warnings = results.filter((r) => r.status === 'warning').length;
  const failed = results.filter((r) => r.status === 'failed').length;
  const total = results.length;

  console.log(`Total Endpoints: ${total}`);
  console.log(`✅ Successful: ${successful} (${((successful / total) * 100).toFixed(1)}%)`);
  console.log(`⚠️  Warnings: ${warnings} (${((warnings / total) * 100).toFixed(1)}%)`);
  console.log(`❌ Failed: ${failed} (${((failed / total) * 100).toFixed(1)}%)`);

  if (failed > 0) {
    console.log('\n❌ Failed Endpoints:');
    results
      .filter((r) => r.status === 'failed')
      .forEach((r) => {
        console.log(`   - ${r.url}`);
        r.errors?.forEach((e) => console.log(`     ${e}`));
      });
  }

  if (warnings > 0) {
    console.log('\n⚠️  Endpoints with Warnings:');
    results
      .filter((r) => r.status === 'warning')
      .forEach((r) => {
        console.log(`   - ${r.url}`);
        r.warnings?.forEach((w) => console.log(`     ${w}`));
      });
  }

  console.log('\n' + '='.repeat(80));
}

/**
 * Main validation process
 */
async function main() {
  console.log('🚀 Starting ArcGIS Endpoint Validation\n');
  console.log('=' .repeat(80) + '\n');

  // Read connections manifest
  const manifestPath = path.join(__dirname, '..', 'frontend', 'lib', 'connections.json');

  if (!fs.existsSync(manifestPath)) {
    console.error('❌ connections.json not found. Run discover-gis-services.ts first.');
    process.exit(1);
  }

  const manifestData = fs.readFileSync(manifestPath, 'utf-8');
  const manifest: ConnectionManifest = JSON.parse(manifestData);

  console.log('📋 Loaded connection manifest');
  console.log(`   Parcels: ${manifest.parcels ? '✅' : '❌'}`);
  console.log(`   Zoning: ${manifest.zoning ? '✅' : '❌'}`);
  console.log(`   Historic: ${manifest.historic ? '✅' : '❌'}`);
  console.log(`   Coastal: ${manifest.coastal ? '✅' : '❌'}`);
  console.log(`   Flood: ${manifest.flood ? '✅' : '❌'}`);
  console.log(`   Transit: ${manifest.transit ? '✅' : '❌'}`);
  console.log(`   Parking: ${manifest.parking ? '✅' : '❌'}`);
  console.log(`   Setbacks: ${manifest.setbacks ? '✅' : '❌'}`);
  console.log(`   Overlays: ${manifest.overlays?.length || 0} layers`);
  console.log(`   Hazards: ${manifest.hazards?.length || 0} layers`);

  // Validate all endpoints
  const results = await validateManifest(manifest);

  // Generate summary
  generateSummary(results);

  // Save validation report
  const reportPath = path.join(__dirname, '..', 'frontend', 'lib', 'validation-report.json');
  fs.writeFileSync(reportPath, JSON.stringify(results, null, 2));
  console.log(`\n✅ Validation report saved to: ${reportPath}`);

  // Exit with error code if any endpoints failed
  const failedCount = results.filter((r) => r.status === 'failed').length;
  if (failedCount > 0) {
    process.exit(1);
  }
}

// Run validation
main().catch(console.error);
