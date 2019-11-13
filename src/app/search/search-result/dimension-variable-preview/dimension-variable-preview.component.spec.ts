import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DimensionVariablePreviewComponent } from './dimension-variable-preview.component';

describe('DimensionVariablePreviewComponent', () => {
  let component: DimensionVariablePreviewComponent;
  let fixture: ComponentFixture<DimensionVariablePreviewComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DimensionVariablePreviewComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DimensionVariablePreviewComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
