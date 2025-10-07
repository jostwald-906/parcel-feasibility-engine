import type { ParcelAnalysis } from './arcgis-client';

/**
 * Combine multiple parcels into a single analysis
 * Useful for assemblage projects where owner controls multiple adjacent parcels
 */
export function combineParcels(parcels: ParcelAnalysis[]): ParcelAnalysis {
  if (parcels.length === 0) {
    throw new Error('No parcels to combine');
  }

  if (parcels.length === 1) {
    return parcels[0];
  }

  // Combine lot sizes
  const totalLotSize = parcels.reduce((sum, p) => sum + (p.parcel.lotSizeSqft || 0), 0);

  // Combine existing units and building sqft
  const totalUnits = parcels.reduce((sum, p) => sum + (p.parcel.units || 0), 0);
  const totalBuildingSqft = parcels.reduce((sum, p) => sum + (p.parcel.sqft || 0), 0);

  // Get APNs
  const apns = parcels.map(p => p.parcel.apn).join(', ');

  // Use first parcel's address with "& adjacent parcels"
  const address = `${parcels[0].parcel.address} & ${parcels.length - 1} adjacent parcel${parcels.length > 2 ? 's' : ''}`;

  // Check zoning consistency - warn if mixed
  const uniqueZones = [...new Set(parcels.map(p => p.zoning.zoneCode))];
  const zoning = uniqueZones.length === 1
    ? parcels[0].zoning
    : {
        zoneCode: uniqueZones.join('/'),
        zoneDescription: `Mixed: ${uniqueZones.join(', ')}`,
        majorCategory: parcels[0].zoning.majorCategory,
      };

  // Combine constraints (any parcel with constraint = combined has constraint)
  const historic = {
    isHistoric: parcels.some(p => p.historic.isHistoric),
    resourceName: parcels.filter(p => p.historic.resourceName).map(p => p.historic.resourceName).join(', '),
  };

  const coastal = {
    inCoastalZone: parcels.some(p => p.coastal.inCoastalZone),
    zoneType: parcels.find(p => p.coastal.zoneType)?.coastal.zoneType,
  };

  const flood = {
    inFloodZone: parcels.some(p => p.flood.inFloodZone),
    fldZone: parcels.find(p => p.flood.fldZone)?.flood.fldZone,
    floodway: parcels.some(p => p.flood.floodway),
  };

  // Transit - use most accessible
  const transitParcels = parcels.filter(p => p.transit.withinHalfMile);
  const transit = transitParcels.length > 0
    ? transitParcels[0].transit
    : parcels[0].transit;

  // Hazards - combine all
  const hazards = {
    faultZone: parcels.some(p => p.hazards.faultZone),
    liquefactionZone: parcels.some(p => p.hazards.liquefactionZone),
    landslideZone: parcels.some(p => p.hazards.landslideZone),
    seismicHazardZone: parcels.some(p => p.hazards.seismicHazardZone),
  };

  // Combine overlays
  const allOverlays = parcels.flatMap(p => p.overlays || []);
  const uniqueOverlays = allOverlays.filter((overlay, index, self) =>
    index === self.findIndex(o => o.name === overlay.name)
  );

  // Calculate average center point
  const validParcels = parcels.filter(p => p.parcel.latitude && p.parcel.longitude);
  const avgLat = validParcels.length > 0
    ? validParcels.reduce((sum, p) => sum + (p.parcel.latitude || 0), 0) / validParcels.length
    : undefined;
  const avgLng = validParcels.length > 0
    ? validParcels.reduce((sum, p) => sum + (p.parcel.longitude || 0), 0) / validParcels.length
    : undefined;

  // Estimate combined dimensions (simplified - treats as rectangle)
  const lotWidth = Math.sqrt(totalLotSize * 1.5); // Rough estimate assuming not-quite-square lot
  const lotDepth = totalLotSize / lotWidth;

  return {
    parcel: {
      apn: apns,
      ain: parcels.map(p => p.parcel.ain).filter(Boolean).join(', '),
      address,
      situsFullAddress: address,
      city: parcels[0].parcel.city,
      zip: parcels[0].parcel.zip,
      useCode: parcels[0].parcel.useCode,
      useDescription: `Combined Assembly (${parcels.length} parcels)`,
      yearBuilt: Math.min(...parcels.map(p => parseInt(p.parcel.yearBuilt || '9999')).filter(y => y < 9999)).toString(),
      units: totalUnits,
      sqft: totalBuildingSqft,
      lotSizeSqft: totalLotSize,
      lotWidth: Math.round(lotWidth),
      lotDepth: Math.round(lotDepth),
      latitude: avgLat,
      longitude: avgLng,
      geometry: parcels[0].parcel.geometry, // Use first parcel geometry (could be improved)
    },
    zoning,
    historic,
    coastal,
    flood,
    transit,
    parking: parcels[0].parking,
    setbacks: parcels[0].setbacks,
    hazards,
    overlays: uniqueOverlays,
    environmental: {
      inWetlands: parcels.some(p => p.environmental.inWetlands),
      inConservationArea: parcels.some(p => p.environmental.inConservationArea),
      fireHazardZone: parcels.find(p => p.environmental.fireHazardZone)?.environmental.fireHazardZone || null,
      nearHazardousWaste: parcels.some(p => p.environmental.nearHazardousWaste),
      inEarthquakeFaultZone: parcels.some(p => p.environmental.inEarthquakeFaultZone),
    },
    street: parcels[0].street,
  };
}

/**
 * Generate a summary of multiple parcels for display
 */
export function getMultiParcelSummary(parcels: ParcelAnalysis[]) {
  const totalLotSize = parcels.reduce((sum, p) => sum + (p.parcel.lotSizeSqft || 0), 0);
  const uniqueZones = [...new Set(parcels.map(p => p.zoning.zoneCode))];
  const hasHistoric = parcels.some(p => p.historic.isHistoric);
  const hasCoastal = parcels.some(p => p.coastal.inCoastalZone);
  const hasFlood = parcels.some(p => p.flood.inFloodZone);
  const hasTransit = parcels.some(p => p.transit.withinHalfMile);

  return {
    count: parcels.length,
    totalLotSize,
    zoning: uniqueZones.length === 1 ? uniqueZones[0] : `Mixed (${uniqueZones.join(', ')})`,
    constraints: {
      historic: hasHistoric,
      coastal: hasCoastal,
      flood: hasFlood,
      transit: hasTransit,
    },
  };
}
