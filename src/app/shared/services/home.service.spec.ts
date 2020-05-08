import { TestBed } from '@angular/core/testing';
import { SpectatorService, createServiceFactory } from '@ngneat/spectator';
import { HomeService } from './home.service';
import { HttpClientModule, HttpClient } from '@angular/common/http';

describe('HomeService', () => {

  let spectator: SpectatorService<HomeService>;
  const createService = createServiceFactory({
    service: HomeService,
    imports: [
      HttpClientModule
    ],
    providers: [
      HttpClient
    ]
  });

  beforeEach(() => spectator = createService());

  it('should be created', () => {
    expect(spectator.service).toBeTruthy();
  });
});
