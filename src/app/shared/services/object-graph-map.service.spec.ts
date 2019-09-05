import { TestBed } from '@angular/core/testing';

import { ObjectGraphMapService } from './object-graph-map.service';

describe('ObjectGraphMapService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: ObjectGraphMapService = TestBed.get(ObjectGraphMapService);
    expect(service).toBeTruthy();
  });
});
