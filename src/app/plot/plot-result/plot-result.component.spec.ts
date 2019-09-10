import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PlotResultComponent } from './plot-result.component';

describe('PlotResultComponent', () => {
  let component: PlotResultComponent;
  let fixture: ComponentFixture<PlotResultComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PlotResultComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PlotResultComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
