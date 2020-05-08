import { TestBed } from '@angular/core/testing';
import { createServiceFactory, SpectatorService } from '@ngneat/spectator';
import { AuthGuardService } from './auth-guard.service';
import { HttpClient } from '@angular/common/http';
import { HttpClientModule } from '@angular/common/http';
import { JwtHelperService, JWT_OPTIONS } from '@auth0/angular-jwt';
import { RouterModule } from '@angular/router';

describe('AuthGuardService', () => {
  let spectator: SpectatorService<AuthGuardService>;
  const createService = createServiceFactory({
    service: AuthGuardService,
    providers: [
      HttpClient,
      JwtHelperService,
      {
        provide: JWT_OPTIONS,
        useValue: JWT_OPTIONS
      }
    ],
    imports: [
      HttpClientModule,
      RouterModule.forRoot([])
    ]
  });

  beforeEach(() => spectator = createService());

  it('should be created', () => {
    expect(spectator.service).toBeTruthy();
  });
});
