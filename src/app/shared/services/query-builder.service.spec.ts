import { TestBed } from '@angular/core/testing';
import { SpectatorService, createServiceFactory } from '@ngneat/spectator';
import { HttpClientModule } from '@angular/common/http';
import { QueryBuilderService } from './query-builder.service';
import { RouterModule } from '@angular/router';

describe('QueryBuilderService', () => {

  let spectator: SpectatorService<QueryBuilderService>;
  const createService = createServiceFactory({
    service: QueryBuilderService,
    imports: [
      HttpClientModule,
      RouterModule.forRoot([])
    ]
  });

  beforeEach(() => spectator = createService());

  it('should be created', () => {
    expect(spectator.service).toBeTruthy();
  });
});
