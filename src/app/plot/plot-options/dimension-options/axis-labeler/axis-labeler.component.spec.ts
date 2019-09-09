import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { AxisLabelerComponent } from './axis-labeler.component';

describe('AxisLabelerComponent', () => {
  let component: AxisLabelerComponent;
  let fixture: ComponentFixture<AxisLabelerComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ AxisLabelerComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AxisLabelerComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
