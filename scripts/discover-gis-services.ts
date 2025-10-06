#!/usr/bin/env ts-node
/**
 * ArcGIS Service Discovery Script
 *
 * Crawls Santa Monica's ArcGIS server to automatically discover and validate
 * all relevant services for the Parcel Feasibility Engine.
 *
 * Usage: npx ts-node scripts/discover-gis-services.ts
 */

interface ArcGISLayer {
  id: number;
  name: string;
  type: string;
  geometryType?: string;
  fields?: Array<{ name: string; type: string }>;
}

interface ArcGISService {
  name: string;
  type: string;
  url: string;
}

interface ServiceEndpoint {
  url: string;
  layerName?: string;
  layerId?: number;
  geometryType?: string;
  fields?: Record<string, string>; // field name -> field type
  keyFields?: string[];
}

interface ConnectionManifest {
  parcels?: ServiceEndpoint;
  zoning?: ServiceEndpoint;
  overlays?: ServiceEndpoint[];
  historic?: ServiceEndpoint;
  coastal?: ServiceEndpoint;
  flood?: ServiceEndpoint;
  transit?: ServiceEndpoint;
  setbacks?: ServiceEndpoint;
  parking?: ServiceEndpoint;
  hazards?: ServiceEndpoint[];
}

const BASE_URL = 'https://gis.santamonica.gov/server/rest/services';

// Service identification keywords
const SERVICE_KEYWORDS = {
  parcels: ['parcel', 'assessor', 'apn', 'tax'],
  zoning: ['zoning', 'land_use', 'landuse', 'zone'],
  historic: ['historic', 'preservation', 'landmark', 'heritage'],
  coastal: ['coastal', 'coast'],
  flood: ['fema', 'flood', 'nfhl', 'hazard'],
  transit: ['metro', 'transit', 'bus', 'bbb', 'rail', 'expo'],
  parking: ['parking', 'unbundled'],
  setbacks: ['setback', 'standard'],
  overlays: ['overlay', 'specific', 'plan', 'community', 'dcp', 'downtown'],
  hazards: ['fault', 'liquefaction', 'landslide', 'seismic', 'hazard'],
};

// Field identification patterns
const FIELD_PATTERNS = {
  apn: /^(apn|ain|assessor|parcel.*id)/i,
  address: /^(address|situs|street|location)/i,
  zone: /^(zone|zoning|zone.*code)/i,
  overlay: /^(overlay|plan|district|area)/i,
  historic: /^(hist|status|resource|landmark)/i,
  flood: /^(fld.*zone|zone|bfe)/i,
  transit: /^(stop|station|route|mode|type)/i,
  setback: /^(front|side|rear|setback)/i,
  parking: /^(parking|unbundled)/i,
  hazard: /^(fault|liquefaction|landslide|hazard)/i,
};

/**
 * Fetch and parse JSON from ArcGIS REST endpoint
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
 * List all services in the directory
 */
async function listServices(): Promise<ArcGISService[]> {
  console.log('📡 Discovering services at:', BASE_URL);

  const data = await fetchJSON(BASE_URL);
  if (!data) return [];

  const services: ArcGISService[] = [];

  // Parse FeatureServers
  if (data.services) {
    for (const svc of data.services) {
      if (svc.type === 'FeatureServer' || svc.type === 'MapServer') {
        services.push({
          name: svc.name,
          type: svc.type,
          url: `${BASE_URL}/${svc.name}/${svc.type}`,
        });
      }
    }
  }

  // Parse folders
  if (data.folders) {
    for (const folder of data.folders) {
      const folderData = await fetchJSON(`${BASE_URL}/${folder}`);
      if (folderData?.services) {
        for (const svc of folderData.services) {
          if (svc.type === 'FeatureServer' || svc.type === 'MapServer') {
            services.push({
              name: svc.name,
              type: svc.type,
              url: `${BASE_URL}/${svc.name}/${svc.type}`,
            });
          }
        }
      }
    }
  }

  console.log(`✅ Found ${services.length} services\n`);
  return services;
}

/**
 * Inspect a service and return its layers with metadata
 */
async function inspectService(service: ArcGISService): Promise<ArcGISLayer[]> {
  const data = await fetchJSON(service.url);
  if (!data?.layers) return [];

  return data.layers.map((layer: any) => ({
    id: layer.id,
    name: layer.name,
    type: layer.type,
    geometryType: layer.geometryType,
  }));
}

/**
 * Get detailed layer information including fields
 */
async function getLayerDetails(serviceUrl: string, layerId: number): Promise<any> {
  return await fetchJSON(`${serviceUrl}/${layerId}`);
}

/**
 * Match service to category based on keywords
 */
function categorizeService(serviceName: string): string[] {
  const categories: string[] = [];
  const lowerName = serviceName.toLowerCase();

  for (const [category, keywords] of Object.entries(SERVICE_KEYWORDS)) {
    if (keywords.some(keyword => lowerName.includes(keyword))) {
      categories.push(category);
    }
  }

  return categories;
}

/**
 * Identify key fields in a layer
 */
function identifyKeyFields(fields: any[]): Record<string, string[]> {
  const keyFields: Record<string, string[]> = {};

  for (const [category, pattern] of Object.entries(FIELD_PATTERNS)) {
    const matches = fields
      .filter(f => pattern.test(f.name))
      .map(f => f.name);

    if (matches.length > 0) {
      keyFields[category] = matches;
    }
  }

  return keyFields;
}

/**
 * Main discovery process
 */
async function discoverServices(): Promise<ConnectionManifest> {
  const manifest: ConnectionManifest = {
    overlays: [],
    hazards: [],
  };

  const services = await listServices();

  for (const service of services) {
    const categories = categorizeService(service.name);
    if (categories.length === 0) continue;

    console.log(`🔍 Inspecting: ${service.name}`);
    console.log(`   Categories: ${categories.join(', ')}`);

    const layers = await inspectService(service);

    for (const layer of layers) {
      const details = await getLayerDetails(service.url, layer.id);
      if (!details) continue;

      const keyFields = identifyKeyFields(details.fields || []);
      const fieldNames = (details.fields || []).reduce((acc: any, f: any) => {
        acc[f.name] = f.type;
        return acc;
      }, {});

      const endpoint: ServiceEndpoint = {
        url: `${service.url}/${layer.id}`,
        layerName: layer.name,
        layerId: layer.id,
        geometryType: details.geometryType,
        fields: fieldNames,
        keyFields: Object.keys(keyFields),
      };

      console.log(`   Layer ${layer.id}: ${layer.name} (${details.geometryType})`);
      console.log(`   Key fields: ${Object.keys(keyFields).join(', ') || 'none'}\n`);

      // Assign to manifest categories
      for (const category of categories) {
        if (category === 'parcels' && keyFields.apn && !manifest.parcels) {
          manifest.parcels = endpoint;
        } else if (category === 'zoning' && keyFields.zone && !manifest.zoning) {
          manifest.zoning = endpoint;
        } else if (category === 'historic' && keyFields.historic && !manifest.historic) {
          manifest.historic = endpoint;
        } else if (category === 'coastal' && !manifest.coastal) {
          manifest.coastal = endpoint;
        } else if (category === 'flood' && keyFields.flood && !manifest.flood) {
          manifest.flood = endpoint;
        } else if (category === 'transit' && keyFields.transit && !manifest.transit) {
          manifest.transit = endpoint;
        } else if (category === 'parking' && keyFields.parking && !manifest.parking) {
          manifest.parking = endpoint;
        } else if (category === 'setbacks' && keyFields.setback && !manifest.setbacks) {
          manifest.setbacks = endpoint;
        } else if (category === 'overlays') {
          manifest.overlays!.push(endpoint);
        } else if (category === 'hazards') {
          manifest.hazards!.push(endpoint);
        }
      }
    }
  }

  return manifest;
}

/**
 * Main execution
 */
async function main() {
  console.log('🚀 Starting ArcGIS Service Discovery\n');
  console.log('=' .repeat(80) + '\n');

  const manifest = await discoverServices();

  console.log('\n' + '=' .repeat(80));
  console.log('📋 DISCOVERY COMPLETE\n');

  console.log('Discovered Endpoints:');
  console.log(JSON.stringify(manifest, null, 2));

  // Write to file
  const fs = await import('fs');
  const path = await import('path');
  const { fileURLToPath } = await import('url');
  const __dirname = path.dirname(fileURLToPath(import.meta.url));
  const outputPath = path.join(__dirname, '..', 'frontend', 'lib', 'connections.json');

  fs.writeFileSync(outputPath, JSON.stringify(manifest, null, 2));
  console.log(`\n✅ Saved to: ${outputPath}`);

  // Generate summary
  console.log('\n📊 Summary:');
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
}

// Run if executed directly
main().catch(console.error);

export { discoverServices, type ConnectionManifest, type ServiceEndpoint };
