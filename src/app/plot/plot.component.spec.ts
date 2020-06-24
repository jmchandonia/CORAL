import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterModule } from '@angular/router';
import { PlotComponent } from './plot.component';
import { Spectator, createComponentFactory } from '@ngneat/spectator';

describe('PlotComponent', () => {

  let spectator: Spectator<PlotComponent>;
  const createComponent = createComponentFactory({
    component: PlotComponent,
    imports: [
      RouterModule.forRoot([])
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });

  it('should have router outlet', () => {
    expect(spectator.query('router-outlet')).toBeTruthy();
  });
});
