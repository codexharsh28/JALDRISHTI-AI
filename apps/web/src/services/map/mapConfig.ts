/**
 * Centralized Map Runtime Configuration for JALDRISHTI AI
 * 
 * Supports configurable map providers (OpenStreetMap, MapTiler, Mapbox, Carto, Offline)
 * Handles public client-side keys securely through Vite environment variables.
 */

export type MapProviderId = 'osm' | 'carto' | 'maptiler' | 'mapbox' | 'offline';

export interface MapRuntimeConfig {
  providerId: MapProviderId;
  providerName: string;
  tileUrl: string;
  attribution: string;
  maxZoom: number;
  minZoom: number;
  requiresKey: boolean;
  isKeyConfigured: boolean;
  diagnosticMessage?: string;
}

export class MapConfigService {
  public static getRuntimeConfig(): MapRuntimeConfig {
    // Read Vite environment variables (client-safe public tokens only)
    const envProvider = (import.meta.env.VITE_MAP_PROVIDER || 'osm').toLowerCase() as MapProviderId;
    const apiKey = import.meta.env.VITE_MAP_API_KEY || '';
    const customStyleUrl = import.meta.env.VITE_MAP_STYLE_URL || '';

    const isKeyPresent = Boolean(apiKey && apiKey.trim().length > 0);

    switch (envProvider) {
      case 'maptiler': {
        if (!isKeyPresent && !customStyleUrl) {
          return {
            providerId: 'maptiler',
            providerName: 'MapTiler (Dark)',
            tileUrl: '',
            attribution: '&copy; <a href="https://www.maptiler.com/copyright/" target="_blank">MapTiler</a> &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors',
            maxZoom: 19,
            minZoom: 6,
            requiresKey: true,
            isKeyConfigured: false,
            diagnosticMessage: 'LIVE MAP PROVIDER NOT CONFIGURED (VITE_MAP_API_KEY missing for MapTiler)'
          };
        }
        const style = customStyleUrl || 'streets-v2-dark';
        return {
          providerId: 'maptiler',
          providerName: 'MapTiler',
          tileUrl: `https://api.maptiler.com/maps/${style}/256/{z}/{x}/{y}.png?key=${apiKey}`,
          attribution: '&copy; <a href="https://www.maptiler.com/copyright/" target="_blank">MapTiler</a> &copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors',
          maxZoom: 19,
          minZoom: 6,
          requiresKey: true,
          isKeyConfigured: true
        };
      }

      case 'mapbox': {
        if (!isKeyPresent && !customStyleUrl) {
          return {
            providerId: 'mapbox',
            providerName: 'Mapbox Dark',
            tileUrl: '',
            attribution: '&copy; <a href="https://www.mapbox.com/about/maps/">Mapbox</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
            maxZoom: 19,
            minZoom: 6,
            requiresKey: true,
            isKeyConfigured: false,
            diagnosticMessage: 'LIVE MAP PROVIDER NOT CONFIGURED (VITE_MAP_API_KEY missing for Mapbox)'
          };
        }
        const style = customStyleUrl || 'dark-v11';
        return {
          providerId: 'mapbox',
          providerName: 'Mapbox',
          tileUrl: `https://api.mapbox.com/styles/v1/mapbox/${style}/tiles/{z}/{x}/{y}?access_token=${apiKey}`,
          attribution: '&copy; <a href="https://www.mapbox.com/about/maps/">Mapbox</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
          maxZoom: 19,
          minZoom: 6,
          requiresKey: true,
          isKeyConfigured: true
        };
      }

      case 'carto': {
        // CartoCDN dark basemap
        return {
          providerId: 'carto',
          providerName: 'CARTO Dark Matter',
          tileUrl: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
          maxZoom: 19,
          minZoom: 6,
          requiresKey: false,
          isKeyConfigured: true
        };
      }

      case 'offline': {
        return {
          providerId: 'offline',
          providerName: 'Local Vector Geometry (Offline)',
          tileUrl: '',
          attribution: 'JALDRISHTI AI Local Vector Geometry (Offline Mode)',
          maxZoom: 16,
          minZoom: 7,
          requiresKey: false,
          isKeyConfigured: true
        };
      }

      case 'osm':
      default: {
        // OpenStreetMap Standard Tiles (Public open-access)
        return {
          providerId: 'osm',
          providerName: 'OpenStreetMap (Public)',
          tileUrl: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
          maxZoom: 19,
          minZoom: 6,
          requiresKey: false,
          isKeyConfigured: true
        };
      }
    }
  }
}
