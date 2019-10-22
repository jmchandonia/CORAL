import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { DataValuesComponent } from './data-values.component';

describe('DataValuesComponent', () => {
  let component: DataValuesComponent;
  let fixture: ComponentFixture<DataValuesComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ DataValuesComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(DataValuesComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
