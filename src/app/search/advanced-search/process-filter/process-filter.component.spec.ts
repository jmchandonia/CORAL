import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ProcessFilterComponent } from './process-filter.component';

describe('ProcessFilterComponent', () => {
  let component: ProcessFilterComponent;
  let fixture: ComponentFixture<ProcessFilterComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ProcessFilterComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ProcessFilterComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
