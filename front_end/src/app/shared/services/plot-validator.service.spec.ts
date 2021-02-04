import { TestBed } from '@angular/core/testing';

import { PlotValidatorService } from './plot-validator.service';

describe('PlotValidatorService', () => {
  let service: PlotValidatorService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(PlotValidatorService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
