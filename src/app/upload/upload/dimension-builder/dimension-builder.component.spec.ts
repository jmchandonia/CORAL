import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DimensionBuilderComponent } from './dimension-builder.component';

describe('DimensionBuilderComponent', () => {
  let component: DimensionBuilderComponent;
  let fixture: ComponentFixture<DimensionBuilderComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DimensionBuilderComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DimensionBuilderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
