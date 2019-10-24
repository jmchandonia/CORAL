import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { LoadSuccessTableComponent } from './load-success-table.component';

describe('LoadSuccessTableComponent', () => {
  let component: LoadSuccessTableComponent;
  let fixture: ComponentFixture<LoadSuccessTableComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ LoadSuccessTableComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(LoadSuccessTableComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
