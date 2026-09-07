import { MapProviderType, MapMode } from '../../types/map';
import { MapConfigService, MapRuntimeConfig } from './mapConfig';

export interface MapProviderConfig {
  type: MapProviderType;
  providerName: string;
  tileUrl: string;
  attribution: string;
  maxZoom: number;
  minZoom: number;
  isOnline: boolean;
  requiresKey: boolean;
  isKeyConfigured: boolean;
  diagnosticMessage?: string;
}

export class MapProviderService {
  public static getRuntimeConfig(): MapProviderConfig {
    const config = MapConfigService.getRuntimeConfig();
    return {
      type: config.providerId === 'offline' ? 'offline' : 'live',
      providerName: config.providerName,
      tileUrl: config.tileUrl,
      attribution: config.attribution,
      maxZoom: config.maxZoom,
      minZoom: config.minZoom,
      isOnline: config.providerId !== 'offline' && config.isKeyConfigured,
      requiresKey: config.requiresKey,
      isKeyConfigured: config.isKeyConfigured,
      diagnosticMessage: config.diagnosticMessage
    };
  }

  public static getFallbackProvider(): MapProviderConfig {
    return {
      type: 'offline',
      providerName: 'Local Vector Geometry (Offline Fallback)',
      tileUrl: '',
      attribution: 'JALDRISHTI AI Local Vector Geometry (Offline Fallback)',
      maxZoom: 16,
      minZoom: 7,
      isOnline: false,
      requiresKey: false,
      isKeyConfigured: true,
      diagnosticMessage: 'OFFLINE MAP — LIMITED GEOGRAPHIC BASEMAP'
    };
  }

  public static resolveMode(isNetworkOnline: boolean, isKeyConfigured: boolean, userProviderType: MapProviderType): MapMode {
    if (!isNetworkOnline) return 'OFFLINE';
    if (!isKeyConfigured) return 'OFFLINE';
    if (userProviderType === 'replay') return 'REPLAY';
    if (userProviderType === 'offline') return 'OFFLINE';
    return 'LIVE';
  }
}
