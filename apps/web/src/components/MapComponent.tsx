import React from 'react';
import { GeospatialOperationsMap, GeospatialMapProps } from './map/GeospatialOperationsMap';

export interface MapComponentProps extends GeospatialMapProps {}

export const MapComponent: React.FC<MapComponentProps> = (props) => {
  return <GeospatialOperationsMap {...props} />;
};
