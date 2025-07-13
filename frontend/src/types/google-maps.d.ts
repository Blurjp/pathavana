// Google Maps API type declarations
declare global {
  interface Window {
    google: {
      maps: {
        Map: new (element: HTMLElement, options?: google.maps.MapOptions) => google.maps.Map;
        Marker: new (options?: google.maps.MarkerOptions) => google.maps.Marker;
        InfoWindow: new (options?: google.maps.InfoWindowOptions) => google.maps.InfoWindow;
        LatLng: new (lat: number, lng: number) => google.maps.LatLng;
        LatLngBounds: new () => google.maps.LatLngBounds;
        TrafficLayer: new () => google.maps.TrafficLayer;
        Size: new (width: number, height: number, widthUnit?: string, heightUnit?: string) => google.maps.Size;
        Point: new (x: number, y: number) => google.maps.Point;
        Polyline: new (options?: google.maps.PolylineOptions) => google.maps.Polyline;
        event: {
          addListener: (instance: any, eventName: string, handler: Function) => google.maps.MapsEventListener;
        };
        MapTypeId: {
          ROADMAP: string;
          SATELLITE: string;
          HYBRID: string;
          TERRAIN: string;
        };
        Animation: {
          BOUNCE: google.maps.Animation;
          DROP: google.maps.Animation;
        };
        SymbolPath: {
          FORWARD_CLOSED_ARROW: google.maps.SymbolPath;
          FORWARD_OPEN_ARROW: google.maps.SymbolPath;
          BACKWARD_CLOSED_ARROW: google.maps.SymbolPath;
          BACKWARD_OPEN_ARROW: google.maps.SymbolPath;
          CIRCLE: google.maps.SymbolPath;
        };
        visualization: {
          HeatmapLayer: new (options?: any) => any;
        };
      };
    };
  }
}

export {};