import { TestBed } from '@angular/core/testing';

import { UploadValidationService } from './upload-validation.service';

describe('UploadValidationService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: UploadValidationService = TestBed.get(UploadValidationService);
    expect(service).toBeTruthy();
  });
});
