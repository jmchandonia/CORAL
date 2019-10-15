import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DimensionVariableFormComponent } from './dimension-variable-form.component';

describe('DimensionVariableFormComponent', () => {
  let component: DimensionVariableFormComponent;
  let fixture: ComponentFixture<DimensionVariableFormComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DimensionVariableFormComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DimensionVariableFormComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
