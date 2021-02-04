import { TestBed } from '@angular/core/testing';
import { SpectatorService, createServiceFactory } from '@ngneat/spectator';
import { HttpClientModule } from '@angular/common/http';
import { UploadService } from './upload.service';

describe('UploadService', () => {
  let spectator: SpectatorService<UploadService>;
  const createService = createServiceFactory({
    service: UploadService,
    imports: [
      HttpClientModule
    ]
  });

  beforeEach(() => spectator = createService());

  it('should be created', () => {
    expect(spectator.service).toBeTruthy();
  });
});
