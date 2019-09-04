import { TestBed } from '@angular/core/testing';

import { QueryBuilderService } from './query-builder.service';

describe('QueryBuilderService', () => {
  beforeEach(() => TestBed.configureTestingModule({}));

  it('should be created', () => {
    const service: QueryBuilderService = TestBed.get(QueryBuilderService);
    expect(service).toBeTruthy();
  });
});
