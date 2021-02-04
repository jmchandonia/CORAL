import { TestBed } from '@angular/core/testing';
import {
  createServiceFactory,
  SpectatorService,
  createHttpFactory,
  HttpMethod,
  SpectatorHttp
} from '@ngneat/spectator';
import { AuthService } from './auth.service';
import { HttpClientModule } from '@angular/common/http';
import { JwtHelperService, JWT_OPTIONS } from '@auth0/angular-jwt';
import { environment } from 'src/environments/environment';

describe('AuthService', () => {
  let spectator: SpectatorService<AuthService>;
  const createService = createServiceFactory({
    service: AuthService,
    imports: [
      HttpClientModule
    ],
    providers: [
      JwtHelperService,
      {
        provide: JWT_OPTIONS,
        useValue: JWT_OPTIONS
      }
    ]
  });

  let httpSpec: SpectatorHttp<AuthService>;
  const createHttp = createHttpFactory(AuthService);

  beforeEach(() => {
    spectator = createService();
    httpSpec = createHttp();
  });

  afterEach(() => localStorage.clear());

  it('should be created', () => {
    expect(spectator.service).toBeTruthy();
  });

  it('should have login method', () => {
    localStorage.setItem(
      'authToken',
      // tslint:disable-next-line:max-line-length
      'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c'
      );
    expect(spectator.service.isAuthenticated()).toBeTruthy();
  });

  it('should reject invalid login', () => {
    const username = 'bad_username';
    const password = 'bad_password';
    httpSpec.service.submitLogin(username, password).subscribe();
    const req = httpSpec.expectOne(`${environment.baseURL}/user_login`, HttpMethod.POST);
    expect(localStorage.getItem('authToken')).toEqual(null);
  });
});
