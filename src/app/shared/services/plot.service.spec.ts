import { TestBed } from '@angular/core/testing';

import { PlotService } from './plot.service';

describe('PlotService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: PlotService = TestBed.get(PlotService);
    expect(service).toBeTruthy();
  });
});
