import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { AxisOptionComponent } from './axis-option.component';

describe('AxisOptionComponent', () => {
  let component: AxisOptionComponent;
  let fixture: ComponentFixture<AxisOptionComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ AxisOptionComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AxisOptionComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
