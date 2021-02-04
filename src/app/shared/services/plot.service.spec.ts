import { TestBed } from '@angular/core/testing';
import { HttpClientModule } from '@angular/common/http';
import { SpectatorService, createServiceFactory } from '@ngneat/spectator';
import { PlotService } from './plot.service';

describe('PlotService', () => {
  let spectator: SpectatorService<PlotService>;
  const createService = createServiceFactory({
    service: PlotService,
    imports: [
      HttpClientModule
    ]
  });

  beforeEach(() => spectator = createService());

  it('should be created', () => {
    expect(spectator.service).toBeTruthy();
  });
});
