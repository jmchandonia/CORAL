import { TestBed } from '@angular/core/testing';

import { MicrotypeTreeService } from './microtype-tree.service';

describe('MicrotypeTreeService', () => {
  let service: MicrotypeTreeService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(MicrotypeTreeService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
