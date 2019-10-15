import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DimensionFormComponent } from './dimension-form.component';

describe('DimensionFormComponent', () => {
  let component: DimensionFormComponent;
  let fixture: ComponentFixture<DimensionFormComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DimensionFormComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DimensionFormComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
