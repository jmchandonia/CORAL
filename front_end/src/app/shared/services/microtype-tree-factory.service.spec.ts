import { TestBed } from '@angular/core/testing';

import { MicrotypeTreeFactoryService } from './microtype-tree-factory.service';

describe('MicrotypeTreeFactoryService', () => {
  let service: MicrotypeTreeFactoryService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(MicrotypeTreeFactoryService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
