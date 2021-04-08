import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { CoreTypeUploadWidgetComponent } from './core-type-upload-widget.component';

describe('CoreTypeUploadWidgetComponent', () => {
  let component: CoreTypeUploadWidgetComponent;
  let fixture: ComponentFixture<CoreTypeUploadWidgetComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ CoreTypeUploadWidgetComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(CoreTypeUploadWidgetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
