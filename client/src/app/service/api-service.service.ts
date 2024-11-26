// api.service.ts
import { Injectable } from '@angular/core';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  getApiUrl(): string {
    if (environment.production) {
      // In production, use the current domain
      return `${window.location.origin}`;
    } else {
      // In development, use the configured API base URL
      return `${environment.apiBaseUrl}`;
    }
  }
}
