import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { AsyncDropdownComponent } from './async-dropdown.component';

describe('AsyncDropdownComponent', () => {
  let component: AsyncDropdownComponent;
  let fixture: ComponentFixture<AsyncDropdownComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ AsyncDropdownComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AsyncDropdownComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
