import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DataValueFormComponent } from './data-value-form.component';

describe('DataValueFormComponent', () => {
  let component: DataValueFormComponent;
  let fixture: ComponentFixture<DataValueFormComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DataValueFormComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DataValueFormComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
