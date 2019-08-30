import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PropertyParamsComponent } from './property-params.component';

describe('PropertyParamsComponent', () => {
  let component: PropertyParamsComponent;
  let fixture: ComponentFixture<PropertyParamsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PropertyParamsComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PropertyParamsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
