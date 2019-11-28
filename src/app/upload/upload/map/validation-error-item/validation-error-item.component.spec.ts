import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ValidationErrorItemComponent } from './validation-error-item.component';

describe('ValidationErrorItemComponent', () => {
  let component: ValidationErrorItemComponent;
  let fixture: ComponentFixture<ValidationErrorItemComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ValidationErrorItemComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ValidationErrorItemComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
