import { TestBed } from '@angular/core/testing';
import { HttpClientModule } from '@angular/common/http';
import { SpectatorService, createServiceFactory } from '@ngneat/spectator';
import { UploadValidationService } from './upload-validation.service';

describe('UploadValidationService', () => {

  let spectator: SpectatorService<UploadValidationService>;
  const createService = createServiceFactory({
    service: UploadValidationService,
    imports: [
      HttpClientModule
    ]
  });

  beforeEach(() => spectator = createService());

  it('should be created', () => {
    expect(spectator.service).toBeTruthy();
  });
});
