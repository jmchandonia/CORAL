import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { DashboardPlotComponent } from './dashboard-plot.component';
import { PlotlyModule } from 'angular-plotly.js';
import * as PlotlyJS from 'plotly.js';
import { HttpClientModule } from '@angular/common/http';

PlotlyModule.plotlyjs = PlotlyJS;

describe('DashboardPlotComponent', () => {
  let spectator: Spectator<DashboardPlotComponent>;
  const createComponent = createComponentFactory({
    component: DashboardPlotComponent,
    imports: [
      PlotlyModule,
      HttpClientModule
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });
});
