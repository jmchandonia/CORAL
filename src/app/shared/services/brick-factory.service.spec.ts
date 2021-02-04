import { TestBed } from '@angular/core/testing';

import { BrickFactoryService } from './brick-factory.service';

xdescribe('BrickFactoryService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: BrickFactoryService = TestBed.get(BrickFactoryService);
    expect(service).toBeTruthy();
  });
});
