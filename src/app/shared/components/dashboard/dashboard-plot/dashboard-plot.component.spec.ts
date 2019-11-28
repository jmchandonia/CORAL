import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DashboardPlotComponent } from './dashboard-plot.component';

describe('DashboardPlotComponent', () => {
  let component: DashboardPlotComponent;
  let fixture: ComponentFixture<DashboardPlotComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DashboardPlotComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DashboardPlotComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
