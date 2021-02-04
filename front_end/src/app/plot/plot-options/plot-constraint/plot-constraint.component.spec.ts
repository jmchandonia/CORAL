import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PlotConstraintComponent } from './plot-constraint.component';

describe('PlotConstraintComponent', () => {
  let component: PlotConstraintComponent;
  let fixture: ComponentFixture<PlotConstraintComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PlotConstraintComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PlotConstraintComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
