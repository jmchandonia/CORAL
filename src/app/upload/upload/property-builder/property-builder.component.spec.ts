import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { PropertyBuilderComponent } from './property-builder.component';

describe('PropertyBuilderComponent', () => {
  let component: PropertyBuilderComponent;
  let fixture: ComponentFixture<PropertyBuilderComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ PropertyBuilderComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(PropertyBuilderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
