import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { DashboardComponent } from './dashboard.component';
import { MockComponent } from 'ng-mocks';
import { DashboardPlotComponent } from './dashboard-plot/dashboard-plot.component';
import { RouterModule } from '@angular/router';

describe('DashboardComponent', () => {
  let spectator: Spectator<DashboardComponent>;
  const createComponent = createComponentFactory({
    component: DashboardComponent,
    entryComponents: [
      MockComponent(DashboardPlotComponent)
    ],
    imports: [
      RouterModule.forRoot([])
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });
});
