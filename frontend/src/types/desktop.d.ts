export {};

declare global {
  interface Window {
    desktopConfig?: {
      apiBaseUrl?: string;
      platform?: string;
    };
  }
}
