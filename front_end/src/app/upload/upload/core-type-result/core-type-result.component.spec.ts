import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { CoreTypeResultComponent } from './core-type-result.component';

describe('CoreTypeResultComponent', () => {
  let component: CoreTypeResultComponent;
  let fixture: ComponentFixture<CoreTypeResultComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ CoreTypeResultComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CoreTypeResultComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
